from hashlib import sha256
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from property_price_forecasting_wape.experiments import ANCHOR_FEATURES, add_anchor_features, fit_full, metrics, model_frame, predict_full, write_json


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def raw_parameters(config, seed, iterations):
    return {
        "iterations": iterations,
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


def segment_metrics(frame, names):
    output = {}
    for name in names:
        output[name] = [{"segment": str(value), **metrics(group["target"], group["prediction"])} for value, group in frame.groupby(name, dropna=False, observed=True)]
    return output


if __name__ == "__main__":
    config = json.loads((ROOT / "configs/experiments.json").read_text(encoding="utf-8"))
    result = json.loads((ROOT / "artifacts/experiment_results.json").read_text(encoding="utf-8"))
    contract = json.loads((ROOT / config["base_contract_file"]).resolve().read_text(encoding="utf-8"))
    market_manifest = json.loads((ROOT / config["with_tsss_feature_manifest_file"]).resolve().read_text(encoding="utf-8"))
    history_manifest = json.loads((ROOT / "artifacts/history_manifest.json").read_text(encoding="utf-8"))
    base = pd.read_json((ROOT / config["base_cleaned_file"]).resolve(), lines=True, compression="gzip")
    market = pd.read_json((ROOT / config["with_tsss_feature_file"]).resolve(), lines=True, compression="gzip")
    history = pd.read_json(ROOT / "artifacts/history_features.jsonl.gz", lines=True, compression="gzip")
    data = add_anchor_features(pd.concat([base, market.drop(columns=["source_excel_row"]), history.drop(columns=["source_excel_row"])], axis=1))
    categorical = contract["categorical_features"]
    numeric = contract["numeric_features"] + market_manifest["market_features"] + history_manifest["features"] + ANCHOR_FEATURES
    features = categorical + numeric
    development = data.loc[data["split"].eq("development")]
    test = data.loc[data["split"].eq("test")]
    component_directory = ROOT / "artifacts/components"
    component_directory.mkdir(parents=True, exist_ok=True)
    residual_log_iterations = 443
    residual_raw_iterations = int(np.median(result["raw_residual_iterations"]))
    residual_log_model = fit_full(development, "target_price_vnd_m2", features, categorical, config["catboost"], config["random_seed"] + 200, "residual_market", residual_log_iterations)
    residual_log_path = component_directory / "residual_market_log.cbm"
    residual_log_model.save_model(residual_log_path)
    fallback = float(development["target_price_vnd_m2"].median())
    development_anchor = development["market_anchor"].fillna(fallback).clip(lower=1.0).to_numpy(dtype=float)
    raw_label = development["target_price_vnd_m2"].to_numpy(dtype=float) - development_anchor
    residual_raw_model = CatBoostRegressor(**raw_parameters(config["catboost"], config["random_seed"] + 300, residual_raw_iterations))
    residual_raw_model.fit(Pool(model_frame(development, features, categorical), label=raw_label, cat_features=categorical))
    residual_raw_path = component_directory / "residual_market_raw.cbm"
    residual_raw_model.save_model(residual_raw_path)
    current_test = pd.read_json((ROOT / config["with_tsss_test_file"]).resolve(), lines=True, compression="gzip").sort_values("row_index")
    if not np.array_equal(current_test["row_index"].to_numpy(dtype=int), test.index.to_numpy(dtype=int)):
        raise RuntimeError("Frozen test alignment failed")
    current_prediction = current_test["prediction"].to_numpy(dtype=float)
    residual_log_prediction = predict_full(residual_log_model, test, features, categorical, "residual_market", fallback)
    test_anchor = test["market_anchor"].fillna(fallback).clip(lower=1.0).to_numpy(dtype=float)
    raw_prediction = np.maximum(test_anchor + residual_raw_model.predict(Pool(model_frame(test, features, categorical), cat_features=categorical)), 1.0)
    final_prediction = (current_prediction + residual_log_prediction + raw_prediction) / 3
    test_frame = pd.DataFrame({
        "row_index": test.index.to_numpy(dtype=int),
        "as_of_date": test["as_of_date"].to_numpy(),
        "target": test["target_price_vnd_m2"].to_numpy(dtype=float),
        "prediction": final_prediction,
        "district": test["district"].to_numpy(),
        "business_advantage": test["business_advantage"].to_numpy(),
        "price_position": test["price_position"].to_numpy(),
        "asset_history": np.where(test["asset_seen_in_development"].to_numpy() == 1, "seen_asset", "new_asset"),
    })
    test_frame["month"] = test_frame["as_of_date"].str.slice(0, 7)
    test_frame["price_band"] = np.where(test_frame["target"] < 60_000_000, "below_60m", np.where(test_frame["target"] < 100_000_000, "60m_to_100m", np.where(test_frame["target"] < 200_000_000, "100m_to_200m", "at_least_200m")))
    test_frame["error"] = test_frame["prediction"] - test_frame["target"]
    test_frame["absolute_error"] = test_frame["error"].abs()
    test_frame["absolute_percentage_error"] = test_frame["absolute_error"] / np.maximum(test_frame["target"], 1.0)
    write_json(ROOT / "artifacts/reused_test_segments.json", segment_metrics(test_frame, ["month", "district", "business_advantage", "price_position", "asset_history", "price_band"]))
    oof = pd.read_json(ROOT / "artifacts/selected_oof_predictions.jsonl.gz", lines=True, compression="gzip")
    calibration_scores = np.sort(np.abs(np.log1p(oof["target"].to_numpy(dtype=float)) - np.log1p(oof["prediction"].to_numpy(dtype=float))))
    calibration = {"method": "split_conformal_absolute_log_residual", "source": "selected_rolling_oof", "levels": {}}
    for level in [0.8, 0.9, 0.95]:
        index = min(int(np.ceil((len(calibration_scores) + 1) * level)) - 1, len(calibration_scores) - 1)
        calibration["levels"][str(level)] = {"qhat_log": float(calibration_scores[index]), "rows": int(len(calibration_scores))}
        qhat = calibration_scores[index]
        test_frame[f"lower_{int(level * 100)}"] = np.maximum(np.expm1(np.log1p(test_frame["prediction"]) - qhat), 1.0)
        test_frame[f"upper_{int(level * 100)}"] = np.expm1(np.log1p(test_frame["prediction"]) + qhat)
    write_json(ROOT / "artifacts/calibration.json", calibration)
    test_frame.to_json(ROOT / "artifacts/reused_test_predictions.jsonl.gz", orient="records", lines=True, compression={"method": "gzip", "compresslevel": 6, "mtime": 0}, force_ascii=False, double_precision=15)
    oof["month"] = oof["as_of_date"].str.slice(0, 7)
    oof["price_band"] = np.where(oof["target"] < 60_000_000, "below_60m", np.where(oof["target"] < 100_000_000, "60m_to_100m", np.where(oof["target"] < 200_000_000, "100m_to_200m", "at_least_200m")))
    write_json(ROOT / "artifacts/oof_segments.json", segment_metrics(oof, ["fold", "month", "district", "business_advantage", "price_position", "price_band"]))
    interval_coverage = {}
    for level in [0.8, 0.9, 0.95]:
        suffix = int(level * 100)
        covered = (test_frame["target"] >= test_frame[f"lower_{suffix}"]) & (test_frame["target"] <= test_frame[f"upper_{suffix}"])
        interval_coverage[str(level)] = float(covered.mean())
    old = json.loads((ROOT / config["without_tsss_selected_file"]).resolve().read_text(encoding="utf-8"))["rolling_metrics"]
    with_tsss = metrics(oof["target"], np.load(ROOT / "artifacts/component_oof_predictions.npz")["with_tsss_frozen"])
    final = {
        "objective": "honest full-population rolling WAPE below 10 percent",
        "target_wape": config["target_wape"],
        "target_reached": result["selected"]["metrics"]["wape"] < config["target_wape"],
        "selected_solution": "equal blend of frozen with-TSSS, log residual market anchor and raw-MAE residual market anchor",
        "rolling_metrics": result["selected"]["metrics"],
        "rolling_comparison": {"without_tsss": old, "with_tsss": with_tsss},
        "reused_test_non_confirmatory": metrics(test_frame["target"], test_frame["prediction"]),
        "reused_test_interval_coverage": interval_coverage,
        "test_used_for_selection": False,
        "component_iterations": {"with_tsss_frozen": 311, "residual_market_log": residual_log_iterations, "residual_market_raw": residual_raw_iterations},
    }
    write_json(ROOT / "artifacts/final_results.json", final)
    manifest = {
        "solution": final["selected_solution"],
        "weights": {"with_tsss_frozen": 1 / 3, "residual_market_log": 1 / 3, "residual_market_raw": 1 / 3},
        "components": {
            "with_tsss_frozen": {"path": config["with_tsss_model_file"], "sha256": digest((ROOT / config["with_tsss_model_file"]).resolve())},
            "residual_market_log": {"path": "artifacts/components/residual_market_log.cbm", "sha256": digest(residual_log_path)},
            "residual_market_raw": {"path": "artifacts/components/residual_market_raw.cbm", "sha256": digest(residual_raw_path)},
        },
        "features": features,
        "history_label_lag_days": config["label_availability_lag_days"],
        "test_is_reused_non_confirmatory": True,
        "production_status": "experiment_not_production_ready",
    }
    write_json(ROOT / "artifacts/solution_manifest.json", manifest)
    print(json.dumps(final, ensure_ascii=False))
