from datetime import datetime, timezone
from pathlib import Path
import gzip
import json
import math

import joblib
import numpy as np
import pandas as pd

from property_price_forecasting.cleaning import CATEGORICAL_FEATURES, NUMERIC_FEATURES
from property_price_forecasting.inference import BASE_NUMERIC_INPUTS, FORBIDDEN_INPUTS, OPTIONAL_INPUTS, REQUIRED_INPUTS, assess_feature_frame, prediction_intervals, predict_records
from property_price_forecasting.modeling import file_sha256, price_band, regression_metrics, segmented_metrics


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def conformal_calibration(oof, levels):
    scores = np.abs(np.log1p(oof["target"].to_numpy(dtype=float)) - np.log1p(oof["prediction"].to_numpy(dtype=float)))
    ordered = np.sort(scores)
    result = {}
    for level in levels:
        index = min(int(math.ceil((len(ordered) + 1) * level)) - 1, len(ordered) - 1)
        result[str(level)] = {"qhat_log": float(ordered[index]), "calibration_rows": int(len(ordered))}
    return {"method": "split_conformal_absolute_log_residual", "source": "rolling_oof_development_only", "levels": result}


def category_counts(dataframe, names):
    output = {}
    for name in names:
        values = dataframe[name].astype(str).value_counts(dropna=False)
        output[name] = {str(key): int(value) for key, value in values.items()}
    return output


def deployment_profile(development, config):
    limits = {}
    for name in BASE_NUMERIC_INPUTS:
        values = development[name].to_numpy(dtype=float)
        limits[name] = {
            "lower": float(np.quantile(values, config["numeric_lower_quantile"])),
            "upper": float(np.quantile(values, config["numeric_upper_quantile"])),
            "median": float(np.median(values)),
        }
    return {
        "development_rows": int(len(development)),
        "development_date_min": str(development["as_of_date"].min()),
        "development_date_max": str(development["as_of_date"].max()),
        "category_counts": category_counts(development, ["district", "ward_new", "road", "price_position", "business_advantage"]),
        "numeric_limits": limits,
        "quantiles": [config["numeric_lower_quantile"], config["numeric_upper_quantile"]],
    }


def monitoring_baseline(development, predictions, decisions, config):
    numeric = {}
    for name in BASE_NUMERIC_INPUTS:
        values = development[name].to_numpy(dtype=float)
        numeric[name] = {
            "p05": float(np.quantile(values, 0.05)),
            "p50": float(np.quantile(values, 0.50)),
            "p95": float(np.quantile(values, 0.95)),
            "missing_rate": float(development[name].isna().mean()),
        }
    categorical = {}
    for name in CATEGORICAL_FEATURES:
        proportions = development[name].astype(str).value_counts(normalize=True).head(20)
        categorical[name] = {str(key): float(value) for key, value in proportions.items()}
    statuses = pd.Series([value["status"] for value in decisions]).value_counts(normalize=True)
    return {
        "reference_population": "development_2024_03_to_2025_04",
        "numeric": numeric,
        "categorical_top20_proportions": categorical,
        "test_prediction_distribution": {
            "p05": float(np.quantile(predictions, 0.05)),
            "p50": float(np.quantile(predictions, 0.50)),
            "p95": float(np.quantile(predictions, 0.95)),
        },
        "test_status_rates": {str(key): float(value) for key, value in statuses.items()},
        "thresholds": config["drift_thresholds"],
    }


def inference_contract(config):
    return {
        "target": "TSTĐ unit land price at as_of_date",
        "unit": "VND/m2",
        "required_inputs": REQUIRED_INPUTS,
        "optional_inputs": OPTIONAL_INPUTS,
        "forbidden_inputs": FORBIDDEN_INPUTS,
        "categorical_features_after_preprocessing": CATEGORICAL_FEATURES,
        "numeric_features_after_preprocessing": NUMERIC_FEATURES,
        "tsss_allowed": False,
        "supported_as_of_start": config["supported_as_of_start"],
        "supported_as_of_end": config["supported_as_of_end"],
        "outside_supported_date_action": "reject",
        "unseen_district_action": "reject",
        "other_out_of_domain_action": "manual_review",
    }


def evaluate_stage4(project_root, config_path):
    root = Path(project_root)
    config = json.loads((root / config_path).read_text(encoding="utf-8"))
    output = root / config["output_directory"]
    package = output / "model_package"
    manifest_path = output / "evaluation_manifest.json"
    if manifest_path.exists():
        raise RuntimeError("Locked test evaluation already exists")
    selected = json.loads((root / config["selected_model_path"]).read_text(encoding="utf-8"))
    model_path = root / config["model_path"]
    if file_sha256(model_path) != selected["model_sha256"]:
        raise RuntimeError("Selected model checksum mismatch")
    data = pd.read_json(root / config["cleaned_data_path"], lines=True, compression="gzip")
    development = data.loc[data["split"].eq("development")].copy()
    test = data.loc[data["split"].eq("test")].copy()
    if len(test) != config["expected_test_rows"]:
        raise RuntimeError("Unexpected locked test row count")
    if test["as_of_date"].min() != config["expected_test_date_min"] or test["as_of_date"].max() != config["expected_test_date_max"]:
        raise RuntimeError("Unexpected locked test date range")
    oof = pd.read_json(root / config["oof_path"], lines=True, compression="gzip")
    if oof["as_of_date"].max() > selected.get("development_date_max", "2025-04-30"):
        if oof["as_of_date"].max() > "2025-04-30":
            raise RuntimeError("Calibration source extends into locked test")
    calibration = conformal_calibration(oof, config["calibration_levels"])
    profile = deployment_profile(development, config)
    model = joblib.load(model_path)
    features = CATEGORICAL_FEATURES + NUMERIC_FEATURES
    predictions = np.maximum(np.expm1(model.predict(test[features])), 1.0)
    intervals = prediction_intervals(predictions, calibration)
    primary = str(config["primary_interval_level"])
    decisions = assess_feature_frame(test[features], test["as_of_date"].tolist(), predictions, intervals[primary]["lower"], intervals[primary]["upper"], profile, config)
    target = test["target_price_vnd_m2"].to_numpy(dtype=float)
    overall = regression_metrics(target, predictions)
    road_counts = development["road"].astype(str).value_counts()
    ward_counts = development["ward_new"].astype(str).value_counts()
    evaluation = pd.DataFrame({
        "evaluation_row_id": np.arange(1, len(test) + 1),
        "as_of_date": test["as_of_date"].to_numpy(),
        "target": target,
        "prediction": predictions,
        "district": test["district"].to_numpy(),
        "ward_new": test["ward_new"].to_numpy(),
        "business_advantage": test["business_advantage"].to_numpy(),
        "price_position": test["price_position"].to_numpy(),
        "warehouse_type": "tstd",
        "asset_history": np.where(test["asset_seen_in_development"].to_numpy() == 1, "seen_asset", "new_asset"),
    })
    evaluation["month"] = evaluation["as_of_date"].str.slice(0, 7)
    evaluation["price_band"] = [price_band(value) for value in target]
    evaluation["road_frequency"] = ["unseen" if road_counts.get(str(value), 0) == 0 else "rare" if road_counts.get(str(value), 0) < config["road_rare_min_count"] else "common" for value in test["road"]]
    evaluation["ward_frequency"] = ["unseen" if ward_counts.get(str(value), 0) == 0 else "rare" if ward_counts.get(str(value), 0) < 10 else "common" for value in test["ward_new"]]
    quality_flags = [name for name in NUMERIC_FEATURES if name.startswith("quality_")]
    evaluation["data_quality"] = np.where(test[quality_flags].max(axis=1).to_numpy() == 1, "flagged", "clean")
    evaluation["status"] = [value["status"] for value in decisions]
    evaluation["flags"] = ["|".join(value["flags"]) for value in decisions]
    evaluation["error"] = predictions - target
    evaluation["absolute_error"] = np.abs(evaluation["error"])
    evaluation["absolute_percentage_error"] = evaluation["absolute_error"] / np.maximum(target, 1.0)
    for level, values in intervals.items():
        suffix = str(int(float(level) * 100))
        evaluation[f"lower_{suffix}"] = values["lower"]
        evaluation[f"upper_{suffix}"] = values["upper"]
    segment_columns = ["month", "district", "ward_new", "road_frequency", "ward_frequency", "price_band", "warehouse_type", "data_quality", "business_advantage", "price_position", "asset_history", "status"]
    segments = segmented_metrics(evaluation, segment_columns)
    coverage = {}
    for level in calibration["levels"]:
        suffix = str(int(float(level) * 100))
        inside = target >= evaluation[f"lower_{suffix}"].to_numpy()
        inside &= target <= evaluation[f"upper_{suffix}"].to_numpy()
        coverage[level] = {"nominal": float(level), "observed": float(inside.mean()), "mean_width_vnd_m2": float((evaluation[f"upper_{suffix}"] - evaluation[f"lower_{suffix}"]).mean())}
    checks = {
        "mae_vnd_m2": overall["mae_vnd_m2"] <= config["acceptance"]["mae_vnd_m2_max"],
        "wape": overall["wape"] <= config["acceptance"]["wape_max"],
        "within_20pct": overall["within_20pct"] >= config["acceptance"]["within_20pct_min"],
    }
    test_metrics = {
        "population": "locked_test_tstd_2025_05_to_2025_07",
        "overall": overall,
        "interval_coverage": coverage,
        "acceptance_thresholds": config["acceptance"],
        "acceptance_checks": checks,
        "accepted": bool(all(checks.values())),
    }
    write_json(output / "calibration.json", calibration)
    write_json(output / "domain_profile.json", profile)
    write_json(output / "test_metrics.json", test_metrics)
    write_json(output / "segment_metrics.json", segments)
    compression = {"method": "gzip", "compresslevel": 6, "mtime": 0}
    evaluation.to_json(output / "test_predictions.jsonl.gz", orient="records", lines=True, compression=compression, force_ascii=False, double_precision=15)
    contract = inference_contract(config)
    baseline = monitoring_baseline(development, predictions, decisions, config)
    write_json(package / "inference_contract.json", contract)
    write_json(package / "monitoring_baseline.json", baseline)
    write_json(package / "example_input.json", [config["example_input"]])
    example_output = predict_records([config["example_input"]], model_path, output / "domain_profile.json", output / "calibration.json", config)
    write_json(package / "example_output.json", example_output)
    package_manifest = {
        "package_version": "1.0.0-stage4",
        "model": "ridge",
        "model_path": config["model_path"],
        "model_sha256": selected["model_sha256"],
        "target_transform": "log1p",
        "parameters": selected["parameters"],
        "calibration_path": "artifacts/stage_04/calibration.json",
        "domain_profile_path": "artifacts/stage_04/domain_profile.json",
        "inference_contract_path": "artifacts/stage_04/model_package/inference_contract.json",
        "supported_as_of_start": config["supported_as_of_start"],
        "supported_as_of_end": config["supported_as_of_end"],
        "accepted_on_locked_test": test_metrics["accepted"],
    }
    write_json(package / "deployment_manifest.json", package_manifest)
    manifest = {
        "evaluation_run_count": 1,
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "test_rows": int(len(test)),
        "test_date_min": str(test["as_of_date"].min()),
        "test_date_max": str(test["as_of_date"].max()),
        "development_rows": int(len(development)),
        "model_sha256": selected["model_sha256"],
        "test_predictions_sha256": file_sha256(output / "test_predictions.jsonl.gz"),
        "test_was_used_for_fit_tuning_or_calibration": False,
        "test_was_used_for_final_evaluation_only": True,
    }
    write_json(manifest_path, manifest)
    return test_metrics
