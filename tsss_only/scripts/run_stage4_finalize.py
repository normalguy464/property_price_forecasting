from pathlib import Path
from hashlib import sha256
import json
import statistics
import sys

import joblib
import numpy as np
import pandas as pd
from catboost import Pool


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str((ROOT / "../without_tsss/src").resolve()))

from property_price_forecasting.modeling import HierarchicalMedianRegressor, build_ridge_pipeline
from tsss_only.modeling import fit_full_catboost, frame_for_catboost, regression_metrics


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def checksum(path):
    digest = sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


if __name__ == "__main__":
    config = json.loads((ROOT / "configs/pipeline.json").read_text(encoding="utf-8"))
    stage2 = ROOT / "artifacts/stage_02"
    stage3 = ROOT / "artifacts/stage_03"
    contract = json.loads((stage2 / "data_contract.json").read_text(encoding="utf-8"))
    benchmark = json.loads((stage3 / "benchmark_results.json").read_text(encoding="utf-8"))
    data = pd.read_json(stage2 / "cleaned_tsss.jsonl.gz", lines=True, compression="gzip")
    development = data.loc[data["split"].eq("development")].copy()
    test = data.loc[data["split"].eq("test")].copy()
    categorical = contract["categorical_features"]
    numeric = contract["numeric_features"]
    features = categorical + numeric
    target = contract["target"]
    selected = benchmark["selected_variant"]
    details = next(value for value in benchmark["candidates"] if value["variant"] == selected)
    model_dir = stage3 / "model"
    model_dir.mkdir(parents=True, exist_ok=True)
    if selected == "hierarchical_median":
        model = HierarchicalMedianRegressor(lookback_months=6, road_min_count=5, ward_min_count=10, district_min_count=20)
        model.fit(development, development[target], config["test_start"])
        prediction = model.predict(test)
        model_path = model_dir / "hierarchical_median.joblib"
        joblib.dump(model, model_path)
        parameters = {"lookback_months": 6, "road_min_count": 5, "ward_min_count": 10, "district_min_count": 20}
    elif selected == "ridge_log":
        model = build_ridge_pipeline(categorical, numeric, config["ridge_alpha"], config["one_hot_min_frequency"])
        model.fit(development[features], np.log1p(development[target].to_numpy(dtype=float)))
        prediction = np.maximum(np.expm1(model.predict(test[features])), 1.0)
        model_path = model_dir / "ridge.joblib"
        joblib.dump(model, model_path)
        parameters = {"alpha": config["ridge_alpha"], "target_transform": "log1p"}
    else:
        iterations = int(statistics.median([item["best_iteration"] for item in details["training"]]))
        model = fit_full_catboost(development, target, features, categorical, config["catboost"], config["random_seed"], selected, config["rare_price_band"], iterations)
        values = model.predict(Pool(frame_for_catboost(test, features, categorical), cat_features=categorical))
        prediction = np.maximum(np.expm1(values), 1.0) if selected != "catboost_raw" else np.maximum(values, 1.0)
        model_path = model_dir / "catboost.cbm"
        model.save_model(model_path)
        parameters = {**config["catboost"], "iterations": iterations, "training_variant": selected}
    test_frame = pd.DataFrame({"source_excel_row": test["source_excel_row"].to_numpy(), "as_of_date": test["as_of_date"].to_numpy(), "target": test[target].to_numpy(dtype=float), "prediction": prediction})
    test_frame["error"] = test_frame["prediction"] - test_frame["target"]
    test_frame["absolute_error"] = test_frame["error"].abs()
    test_frame["absolute_percentage_error"] = test_frame["absolute_error"] / np.maximum(test_frame["target"], 1.0)
    test_frame["asset_history"] = np.where(test["asset_seen_in_development"].to_numpy() == 1, "seen_in_development", "new_asset")
    test_frame.to_json(stage3 / "test_predictions.jsonl.gz", orient="records", lines=True, compression={"method": "gzip", "compresslevel": 6, "mtime": 0}, force_ascii=False, double_precision=15)
    segment_metrics = {
        name: regression_metrics(frame["target"], frame["prediction"])
        for name, frame in test_frame.groupby("asset_history", sort=True)
    }
    result = {
        "selected_model": selected,
        "selection_basis": benchmark["selection_basis"],
        "rolling_metrics": benchmark["selected_pooled"],
        "test_metrics": regression_metrics(test_frame["target"], test_frame["prediction"]),
        "test_metrics_by_asset_history": segment_metrics,
        "test_is_temporal_holdout_not_used_for_selection": True,
        "target": target,
        "target_source_column": contract["target_source_column"],
        "transaction_status_used_as_feature": False,
        "parameters": parameters,
        "model_path": str(model_path.relative_to(ROOT)).replace("\\", "/"),
        "model_sha256": checksum(model_path),
        "development_rows": int(len(development)),
        "test_rows": int(len(test))
    }
    write_json(stage3 / "final_results.json", result)
    print(json.dumps(result, ensure_ascii=False))
