from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str((ROOT / "../without_tsss/src").resolve()))

from property_price_forecasting.modeling import HierarchicalMedianRegressor, fit_predict_ridge
from tsss_only.modeling import fit_predict_catboost, regression_metrics


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def dates_for_fold(data, fold):
    dates = pd.to_datetime(data["as_of_date"], format="%Y-%m-%d")
    return data.loc[dates.between(fold["train_start"], fold["train_end"])], data.loc[dates.between(fold["validation_start"], fold["validation_end"])]


if __name__ == "__main__":
    config = json.loads((ROOT / "configs/pipeline.json").read_text(encoding="utf-8"))
    stage2 = ROOT / "artifacts/stage_02"
    stage3 = ROOT / "artifacts/stage_03"
    contract = json.loads((stage2 / "data_contract.json").read_text(encoding="utf-8"))
    split = json.loads((stage2 / "split_manifest.json").read_text(encoding="utf-8"))
    data = pd.read_json(stage2 / "cleaned_tsss.jsonl.gz", lines=True, compression="gzip")
    development = data.loc[data["split"].eq("development")].copy()
    categorical = contract["categorical_features"]
    numeric = contract["numeric_features"]
    features = categorical + numeric
    target = contract["target"]
    variants = ["hierarchical_median", "ridge_log", "catboost_log", "catboost_raw", "catboost_weighted", "catboost_oversampled"]
    records = {name: [] for name in variants}
    fold_results = {name: [] for name in variants}
    training_details = {name: [] for name in variants if name.startswith("catboost")}
    for fold_index, fold in enumerate(split["folds"]):
        train, validation = dates_for_fold(development, fold)
        baseline = HierarchicalMedianRegressor(lookback_months=6, road_min_count=5, ward_min_count=10, district_min_count=20)
        baseline.fit(train, train[target], fold["validation_start"])
        predictions = {"hierarchical_median": baseline.predict(validation)}
        _, predictions["ridge_log"] = fit_predict_ridge(train, validation, target, categorical, numeric, config["ridge_alpha"], config["one_hot_min_frequency"])
        for name in ["catboost_log", "catboost_raw", "catboost_weighted", "catboost_oversampled"]:
            _, prediction, iteration, details = fit_predict_catboost(train, validation, target, features, categorical, config["catboost"], config["random_seed"] + fold_index, name, config["rare_price_band"])
            predictions[name] = prediction
            training_details[name].append({"fold": fold["name"], "best_iteration": iteration, **details})
        for name, prediction in predictions.items():
            metrics = regression_metrics(validation[target], prediction)
            fold_results[name].append({"fold": fold["name"], **metrics})
            records[name].extend({"row_index": int(index), "fold": fold["name"], "target": float(actual), "prediction": float(value)} for index, actual, value in zip(validation.index, validation[target], prediction))
        print(json.dumps({"fold": fold["name"], "rows": int(len(validation))}, ensure_ascii=False))
    results = []
    oof = []
    for name in variants:
        frame = pd.DataFrame(records[name])
        metrics = regression_metrics(frame["target"], frame["prediction"])
        results.append({"variant": name, "pooled": metrics, "folds": fold_results[name], "training": training_details.get(name, [])})
        frame["variant"] = name
        oof.append(frame)
    selected = min(results, key=lambda value: (value["pooled"][config["primary_metric"]], value["pooled"]["wape"]))
    payload = {
        "selection_basis": "pooled rolling MAPE with WAPE as tie breaker",
        "test_used_for_selection": False,
        "target": contract["target"],
        "target_source_column": contract["target_source_column"],
        "transaction_status_used_as_feature": False,
        "candidates": results,
        "selected_variant": selected["variant"],
        "selected_pooled": selected["pooled"],
        "development_rows": int(len(development)),
        "oof_rows_per_candidate": int(len(records[variants[0]]))
    }
    write_json(stage3 / "benchmark_results.json", payload)
    pd.concat(oof, ignore_index=True).to_json(stage3 / "benchmark_oof_predictions.jsonl.gz", orient="records", lines=True, compression={"method": "gzip", "compresslevel": 6, "mtime": 0}, force_ascii=False, double_precision=15)
    print(json.dumps({"selected": selected["variant"], "metrics": selected["pooled"]}, ensure_ascii=False))
