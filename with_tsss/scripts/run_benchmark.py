from pathlib import Path
import gzip
import json
import sys

import joblib
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from property_price_forecasting_tsss.modeling import build_ridge, file_sha256, fit_predict_catboost, fit_predict_ridge, price_band, regression_metrics, segment_metrics


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def fold_masks(dataframe, fold):
    dates = pd.to_datetime(dataframe["as_of_date"], format="%Y-%m-%d")
    return dates.between(fold["train_start"], fold["train_end"]), dates.between(fold["validation_start"], fold["validation_end"])


def evaluate_ridge_variant(data, folds, categorical, numeric, alpha, minimum_frequency, variant):
    records = []
    fold_results = []
    for fold in folds:
        train_mask, validation_mask = fold_masks(data, fold)
        train = data.loc[train_mask]
        validation = data.loc[validation_mask]
        _, prediction = fit_predict_ridge(train, validation, "target_price_vnd_m2", categorical, numeric, alpha, minimum_frequency)
        metrics = regression_metrics(validation["target_price_vnd_m2"], prediction)
        fold_results.append({"fold": fold["name"], **metrics})
        for index, value in zip(validation.index, prediction):
            records.append({"row_index": int(index), "fold": fold["name"], "prediction": float(value)})
    frame = pd.DataFrame(records)
    target = data.loc[frame["row_index"], "target_price_vnd_m2"].to_numpy(dtype=float)
    metrics = regression_metrics(target, frame["prediction"])
    return {"variant": variant, "parameters": {"alpha": alpha}, "pooled": metrics, "folds": fold_results}, frame


def evaluate_catboost_variant(data, folds, categorical, numeric, config, seed):
    features = categorical + numeric
    records = []
    fold_results = []
    best_iterations = []
    for fold_index, fold in enumerate(folds):
        train_mask, validation_mask = fold_masks(data, fold)
        train = data.loc[train_mask]
        validation = data.loc[validation_mask]
        _, prediction, best_iteration = fit_predict_catboost(train, validation, "target_price_vnd_m2", features, categorical, config, seed + fold_index)
        metrics = regression_metrics(validation["target_price_vnd_m2"], prediction)
        best_iterations.append(best_iteration)
        fold_results.append({"fold": fold["name"], "best_iteration": best_iteration, **metrics})
        for index, value in zip(validation.index, prediction):
            records.append({"row_index": int(index), "fold": fold["name"], "prediction": float(value)})
    frame = pd.DataFrame(records)
    target = data.loc[frame["row_index"], "target_price_vnd_m2"].to_numpy(dtype=float)
    metrics = regression_metrics(target, frame["prediction"])
    return {"variant": "catboost_with_tsss", "parameters": config, "best_iterations": best_iterations, "pooled": metrics, "folds": fold_results}, frame


def enrich_predictions(data, predictions):
    frame = predictions.copy()
    source = data.loc[frame["row_index"]]
    frame["as_of_date"] = source["as_of_date"].to_numpy()
    frame["target"] = source["target_price_vnd_m2"].to_numpy(dtype=float)
    frame["district"] = source["district"].to_numpy()
    frame["business_advantage"] = source["business_advantage"].to_numpy()
    frame["price_position"] = source["price_position"].to_numpy()
    frame["asset_history"] = np.where(source["asset_seen_in_development"].to_numpy() == 1, "seen_asset", "new_asset")
    frame["month"] = frame["as_of_date"].str.slice(0, 7)
    frame["price_band"] = [price_band(value) for value in frame["target"]]
    road_count = source["market_road_count_365d"].to_numpy(dtype=float)
    frame["market_road_coverage"] = np.where(road_count == 0, "none", np.where(road_count < 5, "low", "supported"))
    comparable_count = source["comparable_count_365d"].to_numpy(dtype=float)
    frame["comparable_coverage"] = np.where(comparable_count == 0, "none", np.where(comparable_count < 5, "partial", "top5"))
    frame["error"] = frame["prediction"] - frame["target"]
    frame["absolute_error"] = frame["error"].abs()
    frame["absolute_percentage_error"] = frame["absolute_error"] / np.maximum(frame["target"], 1.0)
    return frame


if __name__ == "__main__":
    config = json.loads((ROOT / "configs/pipeline.json").read_text(encoding="utf-8"))
    contract = json.loads((ROOT / "../without_tsss/artifacts/stage_02/data_contract.json").resolve().read_text(encoding="utf-8"))
    feature_manifest = json.loads((ROOT / "artifacts/feature_manifest.json").read_text(encoding="utf-8"))
    split_manifest = json.loads((ROOT / config["base_split_file"]).resolve().read_text(encoding="utf-8"))
    base = pd.read_json((ROOT / config["base_cleaned_file"]).resolve(), lines=True, compression="gzip")
    market = pd.read_json(ROOT / "artifacts/market_features.jsonl.gz", lines=True, compression="gzip")
    if len(base) != len(market) or not base["source_excel_row"].equals(market["source_excel_row"]):
        raise RuntimeError("Market feature alignment failed")
    data = pd.concat([base.reset_index(drop=True), market.drop(columns=["source_excel_row"]).reset_index(drop=True)], axis=1)
    categorical = contract["categorical_features"]
    base_numeric = contract["numeric_features"]
    market_numeric = feature_manifest["market_features"]
    folds = split_manifest["folds"]
    old_selected = json.loads((ROOT / "../without_tsss/artifacts/stage_03/selected_model.json").resolve().read_text(encoding="utf-8"))
    candidates = [{"variant": "ridge_without_tsss_frozen", "pooled": old_selected["rolling_metrics"], "source": "without_tsss_stage3"}]
    prediction_frames = {}
    ridge_results = []
    for alpha in config["ridge_alphas"]:
        result, predictions = evaluate_ridge_variant(data, folds, categorical, base_numeric + market_numeric, alpha, config["one_hot_min_frequency"], f"ridge_with_tsss_alpha_{alpha}")
        ridge_results.append(result)
        candidates.append(result)
        prediction_frames[result["variant"]] = predictions
        print(json.dumps({"variant": result["variant"], "mae": result["pooled"]["mae_vnd_m2"]}))
    best_ridge = min(ridge_results, key=lambda value: value["pooled"]["mae_vnd_m2"])
    alpha = best_ridge["parameters"]["alpha"]
    aggregate_numeric = [name for name in market_numeric if not name.startswith("comparable_")]
    comparable_numeric = [name for name in market_numeric if name.startswith("comparable_")]
    for variant, selected_market in [("ridge_tsss_aggregate_only", aggregate_numeric), ("ridge_tsss_comparable_only", comparable_numeric)]:
        result, predictions = evaluate_ridge_variant(data, folds, categorical, base_numeric + selected_market, alpha, config["one_hot_min_frequency"], variant)
        candidates.append(result)
        prediction_frames[variant] = predictions
        print(json.dumps({"variant": variant, "mae": result["pooled"]["mae_vnd_m2"]}))
    catboost_result, catboost_predictions = evaluate_catboost_variant(data, folds, categorical, base_numeric + market_numeric, config["catboost"], config["random_seed"])
    candidates.append(catboost_result)
    prediction_frames[catboost_result["variant"]] = catboost_predictions
    print(json.dumps({"variant": catboost_result["variant"], "mae": catboost_result["pooled"]["mae_vnd_m2"]}))
    selectable = [value for value in candidates if value["variant"] != "ridge_without_tsss_frozen"]
    selected = min(selectable, key=lambda value: value["pooled"]["mae_vnd_m2"])
    selected_variant = selected["variant"]
    selected_oof = enrich_predictions(data, prediction_frames[selected_variant])
    development = data.loc[data["split"].eq("development")]
    test = data.loc[data["split"].eq("test")]
    all_features = categorical + base_numeric + market_numeric
    if selected_variant.startswith("ridge"):
        selected_alpha = selected["parameters"]["alpha"]
        model = build_ridge(categorical, base_numeric + market_numeric, selected_alpha, config["one_hot_min_frequency"])
        model.fit(development[all_features], np.log1p(development["target_price_vnd_m2"].to_numpy(dtype=float)))
        test_prediction = np.maximum(np.expm1(model.predict(test[all_features])), 1.0)
        model_path = ROOT / "artifacts/model.joblib"
        joblib.dump(model, model_path)
        model_type = "ridge"
    else:
        from property_price_forecasting_tsss.modeling import catboost_parameters, frame_for_catboost
        best_iterations = selected["best_iterations"]
        parameters = catboost_parameters(config["catboost"], config["random_seed"])
        parameters["iterations"] = int(np.median(best_iterations))
        model = __import__("catboost").CatBoostRegressor(**parameters)
        train_pool = __import__("catboost").Pool(frame_for_catboost(development, all_features, categorical), label=np.log1p(development["target_price_vnd_m2"].to_numpy(dtype=float)), cat_features=categorical)
        model.fit(train_pool)
        test_pool = __import__("catboost").Pool(frame_for_catboost(test, all_features, categorical), cat_features=categorical)
        test_prediction = np.maximum(np.expm1(model.predict(test_pool)), 1.0)
        model_path = ROOT / "artifacts/model.cbm"
        model.save_model(model_path)
        model_type = "catboost"
    test_frame = pd.DataFrame({"row_index": test.index.to_numpy(), "fold": "reused_test", "prediction": test_prediction})
    test_frame = enrich_predictions(data, test_frame)
    old_test_metrics = json.loads((ROOT / config["old_test_metrics_file"]).resolve().read_text(encoding="utf-8"))["overall"]
    results = {
        "selection_basis": "pooled rolling MAE on development only",
        "test_used_for_selection": False,
        "candidates": candidates,
        "selected_variant": selected_variant,
        "selected_model_type": model_type,
        "selected_rolling_metrics": selected["pooled"],
        "reused_test_non_confirmatory": {
            "with_tsss": regression_metrics(test_frame["target"], test_frame["prediction"]),
            "without_tsss_frozen": old_test_metrics,
        },
    }
    write_json(ROOT / "artifacts/benchmark_results.json", results)
    write_json(ROOT / "artifacts/oof_segment_metrics.json", segment_metrics(selected_oof, ["month", "district", "business_advantage", "price_position", "asset_history", "price_band", "market_road_coverage", "comparable_coverage"]))
    write_json(ROOT / "artifacts/test_segment_metrics.json", segment_metrics(test_frame, ["month", "district", "business_advantage", "price_position", "asset_history", "price_band", "market_road_coverage", "comparable_coverage"]))
    compression = {"method": "gzip", "compresslevel": 6, "mtime": 0}
    selected_oof.to_json(ROOT / "artifacts/oof_predictions.jsonl.gz", orient="records", lines=True, compression=compression, force_ascii=False, double_precision=15)
    test_frame.to_json(ROOT / "artifacts/reused_test_predictions.jsonl.gz", orient="records", lines=True, compression=compression, force_ascii=False, double_precision=15)
    model_manifest = {
        "selected_variant": selected_variant,
        "model_type": model_type,
        "model_path": str(model_path.relative_to(ROOT)).replace("\\", "/"),
        "model_sha256": file_sha256(model_path),
        "categorical_features": categorical,
        "base_numeric_features": base_numeric,
        "market_numeric_features": market_numeric,
        "development_rows": int(len(development)),
        "test_rows": int(len(test)),
        "tsss_used_as_target_rows": 0,
        "tsss_used_as_historical_feature_source": True,
        "test_is_reused_non_confirmatory": True,
    }
    write_json(ROOT / "artifacts/model_manifest.json", model_manifest)
    print(json.dumps({"selected": selected_variant, "rolling": selected["pooled"], "reused_test": results["reused_test_non_confirmatory"]}, ensure_ascii=False))
