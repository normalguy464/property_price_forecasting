from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from property_price_forecasting_wape.experiments import ANCHOR_FEATURES, add_anchor_features, metrics, model_frame, write_json


def masks(dataframe, fold):
    dates = pd.to_datetime(dataframe["as_of_date"], format="%Y-%m-%d")
    return dates.between(fold["train_start"], fold["train_end"]), dates.between(fold["validation_start"], fold["validation_end"])


def raw_parameters(config, seed):
    return {
        "iterations": 300,
        "depth": 5,
        "learning_rate": 0.08,
        "l2_leaf_reg": 20.0,
        "random_strength": 0.3,
        "bagging_temperature": 0.3,
        "border_count": 128,
        "max_ctr_complexity": 1,
        "rsm": 0.8,
        "bootstrap_type": "Bayesian",
        "loss_function": "MAE",
        "eval_metric": "MAE",
        "random_seed": seed,
        "thread_count": config["thread_count"],
        "allow_writing_files": False,
        "verbose": False,
    }


def fit_raw_residual(train, validation, features, categorical, config, seed):
    fallback = float(train["target_price_vnd_m2"].median())
    train_anchor = train["market_anchor"].fillna(fallback).clip(lower=1.0).to_numpy(dtype=float)
    validation_anchor = validation["market_anchor"].fillna(fallback).clip(lower=1.0).to_numpy(dtype=float)
    train_label = train["target_price_vnd_m2"].to_numpy(dtype=float) - train_anchor
    validation_label = validation["target_price_vnd_m2"].to_numpy(dtype=float) - validation_anchor
    train_pool = Pool(model_frame(train, features, categorical), label=train_label, cat_features=categorical)
    validation_pool = Pool(model_frame(validation, features, categorical), label=validation_label, cat_features=categorical)
    model = CatBoostRegressor(**raw_parameters(config, seed))
    model.fit(train_pool, eval_set=validation_pool, early_stopping_rounds=40, use_best_model=True)
    prediction = np.maximum(validation_anchor + model.predict(validation_pool), 1.0)
    return prediction, int(model.get_best_iteration() + 1)


def predicted_band(values):
    values = np.asarray(values, dtype=float)
    return np.where(values < 60_000_000, "below_60m", np.where(values < 100_000_000, "60m_to_100m", np.where(values < 200_000_000, "100m_to_200m", "at_least_200m")))


def sequential_correction(prediction, target, fold_names, position, strategy):
    output = np.asarray(prediction, dtype=float).copy()
    target = np.asarray(target, dtype=float)
    fold_names = np.asarray(fold_names)
    position = np.asarray(position)
    ordered_folds = ["fold_1", "fold_2", "fold_3", "fold_4"]
    for fold_index, fold in enumerate(ordered_folds):
        current = fold_names == fold
        prior = np.isin(fold_names, ordered_folds[:fold_index])
        if not prior.any():
            continue
        prior_log_error = np.log1p(target[prior]) - np.log1p(prediction[prior])
        global_log = float(np.median(prior_log_error)) * prior.sum() / (prior.sum() + 100)
        if strategy == "global":
            output[current] = prediction[current] * np.exp(global_log)
            continue
        prior_band = predicted_band(prediction[prior])
        current_band = predicted_band(prediction[current])
        current_indices = np.flatnonzero(current)
        for index, row_index in enumerate(current_indices):
            if strategy == "band":
                group = prior_band == current_band[index]
            else:
                group = (prior_band == current_band[index]) & (position[prior] == position[row_index])
            count = int(group.sum())
            group_log = float(np.median(prior_log_error[group])) if count else global_log
            shrink = count / (count + 50)
            correction = np.clip(np.exp(global_log * (1 - shrink) + group_log * shrink), 0.8, 1.3)
            output[row_index] = prediction[row_index] * correction
    return np.maximum(output, 1.0)


if __name__ == "__main__":
    config = json.loads((ROOT / "configs/experiments.json").read_text(encoding="utf-8"))
    contract = json.loads((ROOT / config["base_contract_file"]).resolve().read_text(encoding="utf-8"))
    split = json.loads((ROOT / config["split_file"]).resolve().read_text(encoding="utf-8"))
    market_manifest = json.loads((ROOT / config["with_tsss_feature_manifest_file"]).resolve().read_text(encoding="utf-8"))
    history_manifest = json.loads((ROOT / "artifacts/history_manifest.json").read_text(encoding="utf-8"))
    base = pd.read_json((ROOT / config["base_cleaned_file"]).resolve(), lines=True, compression="gzip")
    market = pd.read_json((ROOT / config["with_tsss_feature_file"]).resolve(), lines=True, compression="gzip")
    history = pd.read_json(ROOT / "artifacts/history_features.jsonl.gz", lines=True, compression="gzip")
    data = add_anchor_features(pd.concat([base, market.drop(columns=["source_excel_row"]), history.drop(columns=["source_excel_row"])], axis=1))
    categorical = contract["categorical_features"]
    numeric = contract["numeric_features"] + market_manifest["market_features"] + history_manifest["features"] + ANCHOR_FEATURES
    features = categorical + numeric
    component_file = np.load(ROOT / "artifacts/component_oof_predictions.npz")
    row_index = component_file["row_index"].astype(int)
    predictions = {name: component_file[name] for name in component_file.files if name != "row_index"}
    raw_records = []
    raw_iterations = []
    for fold_index, fold in enumerate(split["folds"]):
        train_mask, validation_mask = masks(data, fold)
        train = data.loc[train_mask]
        validation = data.loc[validation_mask]
        prediction, best_iteration = fit_raw_residual(train, validation, features, categorical, config["catboost"], config["random_seed"] + 100 + fold_index)
        raw_iterations.append(best_iteration)
        raw_records.extend(zip(validation.index.to_numpy(dtype=int), prediction.tolist()))
        print(json.dumps({"fold": fold["name"], "best_iteration": best_iteration, "mae": metrics(validation["target_price_vnd_m2"], prediction)["mae_vnd_m2"]}))
    raw_frame = pd.DataFrame(raw_records, columns=["row_index", "prediction"]).sort_values("row_index")
    if not np.array_equal(raw_frame["row_index"].to_numpy(dtype=int), row_index):
        raise RuntimeError("Raw residual alignment failed")
    predictions["residual_market_raw_mae"] = raw_frame["prediction"].to_numpy(dtype=float)
    target = data.loc[row_index, "target_price_vnd_m2"].to_numpy(dtype=float)
    current_oof = pd.read_json((ROOT / config["with_tsss_oof_file"]).resolve(), lines=True, compression="gzip").sort_values("row_index")
    fold_names = current_oof["fold"].to_numpy()
    position = data.loc[row_index, "price_position"].to_numpy()
    candidates = []
    base_combinations = {name: values for name, values in predictions.items()}
    for left, right in [("with_tsss_frozen", "residual_market_raw_mae"), ("residual_market", "residual_market_raw_mae"), ("direct_history", "residual_market_raw_mae")]:
        for right_weight in config["blend_weights"]:
            name = f"blend_{left}_{right}_right_{right_weight}"
            base_combinations[name] = predictions[left] * (1 - right_weight) + predictions[right] * right_weight
    base_combinations["blend_equal_current_log_raw"] = (predictions["with_tsss_frozen"] + predictions["residual_market"] + predictions["residual_market_raw_mae"]) / 3
    base_combinations["blend_current25_log75"] = predictions["with_tsss_frozen"] * 0.25 + predictions["residual_market"] * 0.75
    for name, values in base_combinations.items():
        candidates.append({"name": name, "metrics": metrics(target, values), "details": {"kind": "base"}})
        for strategy in ["global", "band", "band_position"]:
            corrected = sequential_correction(values, target, fold_names, position, strategy)
            corrected_name = f"sequential_{strategy}_{name}"
            predictions[corrected_name] = corrected
            candidates.append({"name": corrected_name, "metrics": metrics(target, corrected), "details": {"kind": "sequential_correction", "base": name, "strategy": strategy}})
    selected = min(candidates, key=lambda value: value["metrics"]["mae_vnd_m2"])
    selected_prediction = predictions.get(selected["name"], base_combinations.get(selected["name"]))
    if selected_prediction is None:
        raise RuntimeError("Selected prediction not found")
    oof = pd.DataFrame({"row_index": row_index, "as_of_date": data.loc[row_index, "as_of_date"].to_numpy(), "fold": fold_names, "target": target, "prediction": selected_prediction, "district": data.loc[row_index, "district"].to_numpy(), "business_advantage": data.loc[row_index, "business_advantage"].to_numpy(), "price_position": position})
    oof["error"] = oof["prediction"] - oof["target"]
    oof["absolute_error"] = oof["error"].abs()
    oof["absolute_percentage_error"] = oof["absolute_error"] / np.maximum(oof["target"], 1.0)
    oof.to_json(ROOT / "artifacts/selected_oof_predictions.jsonl.gz", orient="records", lines=True, compression={"method": "gzip", "compresslevel": 6, "mtime": 0}, force_ascii=False, double_precision=15)
    np.savez_compressed(ROOT / "artifacts/component_oof_predictions.npz", row_index=row_index, **{name: values for name, values in predictions.items() if name in ["with_tsss_frozen", "direct_history", "residual_market", "residual_hybrid", "residual_market_raw_mae"]})
    previous = json.loads((ROOT / "artifacts/experiment_results.json").read_text(encoding="utf-8"))
    result = {
        "selection_population": "rolling_oof_development_only",
        "test_used_for_selection": False,
        "target_wape": config["target_wape"],
        "target_reached": selected["metrics"]["wape"] < config["target_wape"],
        "selected": selected,
        "raw_residual_iterations": raw_iterations,
        "top_candidates": sorted(candidates + previous["top_candidates"], key=lambda value: value["metrics"]["mae_vnd_m2"])[:30],
        "single_models": [value for value in candidates if value["name"] in ["with_tsss_frozen", "direct_history", "residual_market", "residual_hybrid", "residual_market_raw_mae"]],
        "feature_count": previous["feature_count"],
        "categorical_features": previous["categorical_features"],
        "numeric_features": previous["numeric_features"],
    }
    write_json(ROOT / "artifacts/experiment_results.json", result)
    print(json.dumps({"selected": selected, "target_reached": result["target_reached"]}, ensure_ascii=False))
