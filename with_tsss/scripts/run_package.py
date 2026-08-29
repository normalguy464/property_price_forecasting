from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from property_price_forecasting_tsss.inference import FORBIDDEN_INPUTS, OPTIONAL_INPUTS, REQUIRED_INPUTS, predict_records


if __name__ == "__main__":
    config = json.loads((ROOT / "configs/pipeline.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "artifacts/model_manifest.json").read_text(encoding="utf-8"))
    package = ROOT / "artifacts/model_package"
    package.mkdir(parents=True, exist_ok=True)
    model = CatBoostRegressor()
    model.load_model(ROOT / manifest["model_path"])
    names = model.feature_names_
    values = model.get_feature_importance()
    importance = sorted([{"feature": name, "importance": float(value)} for name, value in zip(names, values)], key=lambda item: item["importance"], reverse=True)
    (ROOT / "artifacts/feature_importance.json").write_text(json.dumps(importance, ensure_ascii=False, indent=2), encoding="utf-8")
    contract = {
        "target": "TSTĐ unit land price at as_of_date",
        "unit": "VND/m2",
        "required_tstd_inputs": REQUIRED_INPUTS,
        "optional_tstd_inputs": OPTIONAL_INPUTS,
        "forbidden_tstd_inputs": FORBIDDEN_INPUTS,
        "required_market_source": "TSSS rows with market date and availability date",
        "tsss_as_target_allowed": False,
        "same_report_tsss_allowed": False,
        "supported_as_of_start": config["supported_as_of_start"],
        "supported_as_of_end": config["supported_as_of_end"],
        "low_market_coverage_action": "manual_review",
    }
    (package / "inference_contract.json").write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")
    oof = pd.read_json(ROOT / "artifacts/oof_predictions.jsonl.gz", lines=True, compression="gzip")
    scores = np.sort(np.abs(np.log1p(oof["target"].to_numpy(dtype=float)) - np.log1p(oof["prediction"].to_numpy(dtype=float))))
    levels = {}
    for level in [0.8, 0.9, 0.95]:
        index = min(int(np.ceil((len(scores) + 1) * level)) - 1, len(scores) - 1)
        levels[str(level)] = {"qhat_log": float(scores[index]), "calibration_rows": int(len(scores))}
    calibration = {"method": "split_conformal_absolute_log_residual", "source": "rolling_oof_development_only", "levels": levels}
    (package / "calibration.json").write_text(json.dumps(calibration, ensure_ascii=False, indent=2), encoding="utf-8")
    example = [config["example_input"]]
    (package / "example_input.json").write_text(json.dumps(example, ensure_ascii=False, indent=2), encoding="utf-8")
    source = pd.read_excel((ROOT / config["source_file"]).resolve(), sheet_name=config["source_sheet"])
    output = predict_records(example, source, ROOT / manifest["model_path"], manifest, config, calibration)
    (package / "example_output.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    deployment = {
        "version": "with-tsss-1.0.0",
        "model_path": manifest["model_path"],
        "model_sha256": manifest["model_sha256"],
        "model_type": manifest["model_type"],
        "market_feature_count": len(manifest["market_numeric_features"]),
        "input_contract": "artifacts/model_package/inference_contract.json",
        "calibration": "artifacts/model_package/calibration.json",
        "test_status": "reused_non_confirmatory_only",
        "production_status": "stale_requires_new_data",
    }
    (package / "deployment_manifest.json").write_text(json.dumps(deployment, ensure_ascii=False, indent=2), encoding="utf-8")
    test = pd.read_json(ROOT / "artifacts/reused_test_predictions.jsonl.gz", lines=True, compression="gzip")
    baseline = {
        "reference_population": "development_2024_03_to_2025_04",
        "market_feature_quantiles": {},
        "reused_test_prediction_quantiles": {str(value): float(test["prediction"].quantile(value)) for value in [0.05, 0.5, 0.95]},
        "drift_thresholds": {"psi_warning": 0.2, "missing_rate_absolute_change_warning": 0.05, "market_coverage_rate_change_warning": 0.1, "prediction_median_relative_change_warning": 0.2},
    }
    market_features = pd.read_json(ROOT / "artifacts/market_features.jsonl.gz", lines=True, compression="gzip")
    development_rows = pd.read_json((ROOT / config["base_cleaned_file"]).resolve(), lines=True, compression="gzip")["split"].eq("development")
    for name in ["market_road_count_365d", "market_backoff_count_365d", "comparable_count_365d", "comparable_best_distance_365d"]:
        values = market_features.loc[development_rows.to_numpy(), name]
        baseline["market_feature_quantiles"][name] = {str(value): float(values.quantile(value)) for value in [0.05, 0.5, 0.95]}
    (package / "monitoring_baseline.json").write_text(json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8")
