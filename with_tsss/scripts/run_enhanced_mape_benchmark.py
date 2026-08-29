from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from property_price_forecasting_tsss.modeling import fit_predict_catboost, regression_metrics


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def metrics_with_mape(y_true, y_pred):
    metrics = regression_metrics(y_true, y_pred)
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    metrics["mape"] = float(np.mean(np.abs(y_pred - y_true) / np.maximum(np.abs(y_true), 1.0)))
    return metrics


def evaluate_candidate(data, folds, categorical, features, parameters, seed, name):
    records = []
    fold_results = []
    best_iterations = []
    dates = pd.to_datetime(data["as_of_date"], format="%Y-%m-%d")
    for fold_index, fold in enumerate(folds):
        train = data.loc[dates.between(fold["train_start"], fold["train_end"])]
        validation = data.loc[dates.between(fold["validation_start"], fold["validation_end"])]
        _, prediction, best_iteration = fit_predict_catboost(
            train,
            validation,
            "target_price_vnd_m2",
            features,
            categorical,
            parameters,
            seed + fold_index,
        )
        metrics = metrics_with_mape(validation["target_price_vnd_m2"], prediction)
        fold_results.append({"fold": fold["name"], "best_iteration": best_iteration, **metrics})
        best_iterations.append(best_iteration)
        for index, value in zip(validation.index, prediction):
            records.append({"candidate": name, "row_index": int(index), "fold": fold["name"], "target": float(validation.loc[index, "target_price_vnd_m2"]), "prediction": float(value)})
    frame = pd.DataFrame(records)
    return {
        "candidate": name,
        "feature_count": int(len(features)),
        "parameters": parameters,
        "best_iterations": best_iterations,
        "pooled": metrics_with_mape(frame["target"], frame["prediction"]),
        "folds": fold_results,
    }, frame


if __name__ == "__main__":
    config = json.loads((ROOT / "configs/pipeline.json").read_text(encoding="utf-8"))
    contract = json.loads((ROOT / "../without_tsss/artifacts/stage_02/data_contract.json").resolve().read_text(encoding="utf-8"))
    current_manifest = json.loads((ROOT / "artifacts/feature_manifest.json").read_text(encoding="utf-8"))
    enhanced_manifest = json.loads((ROOT / "artifacts/enhanced_feature_manifest.json").read_text(encoding="utf-8"))
    split_manifest = json.loads((ROOT / config["base_split_file"]).resolve().read_text(encoding="utf-8"))
    model_manifest = json.loads((ROOT / "artifacts/model_manifest.json").read_text(encoding="utf-8"))
    best_parameters = json.loads((ROOT / "artifacts/best_parameters.json").read_text(encoding="utf-8"))
    base = pd.read_json((ROOT / config["base_cleaned_file"]).resolve(), lines=True, compression="gzip")
    current = pd.read_json(ROOT / "artifacts/market_features.jsonl.gz", lines=True, compression="gzip")
    enhanced = pd.read_json(ROOT / "artifacts/enhanced_market_features.jsonl.gz", lines=True, compression="gzip")
    if not base["source_excel_row"].equals(current["source_excel_row"]) or not base["source_excel_row"].equals(enhanced["source_excel_row"]):
        raise RuntimeError("Benchmark feature alignment failed")
    data = pd.concat([
        base.reset_index(drop=True),
        current.drop(columns=["source_excel_row"]).reset_index(drop=True),
        enhanced.drop(columns=["source_excel_row"]).reset_index(drop=True),
    ], axis=1)
    categorical = contract["categorical_features"]
    current_market_features = current_manifest["market_features"]
    base_features = categorical + contract["numeric_features"] + current_market_features
    aggregate_features = [name for name in current_market_features if not name.startswith("comparable_")]
    comparable_replacement_base = categorical + contract["numeric_features"] + aggregate_features
    comparable_v2 = enhanced_manifest["comparable_v2_features"]
    temporal = enhanced_manifest["temporal_market_features"]
    selected_parameters = model_manifest["parameters"]
    variants = [
        ("comparable_v2_replacement_rmse", comparable_replacement_base + comparable_v2, "RMSE"),
        ("temporal_market_rmse", base_features + temporal, "RMSE"),
        ("enhanced_all_rmse", comparable_replacement_base + comparable_v2 + temporal, "RMSE"),
        ("enhanced_all_mae", comparable_replacement_base + comparable_v2 + temporal, "MAE"),
        ("enhanced_all_huber", comparable_replacement_base + comparable_v2 + temporal, "Huber:delta=1.0"),
    ]
    candidates = []
    predictions = []
    evaluation_seed = config["random_seed"] + best_parameters["number"] * 10
    for name, features, loss_function in variants:
        parameters = {**selected_parameters, "loss_function": loss_function, "eval_metric": "MAE"}
        result, frame = evaluate_candidate(data, split_manifest["folds"], categorical, features, parameters, evaluation_seed, name)
        candidates.append(result)
        predictions.append(frame)
        print(json.dumps({"candidate": name, "mape": result["pooled"]["mape"], "wape": result["pooled"]["wape"]}))
    baseline_frame = pd.read_json(ROOT / "artifacts/oof_predictions.jsonl.gz", lines=True, compression="gzip")
    baseline_metrics = metrics_with_mape(baseline_frame["target"], baseline_frame["prediction"])
    baseline_folds = {
        fold: metrics_with_mape(frame["target"], frame["prediction"])
        for fold, frame in baseline_frame.groupby("fold", sort=True)
    }
    for candidate in candidates:
        candidate["folds_improved_mape_vs_baseline"] = int(sum(
            fold["mape"] < baseline_folds[fold["fold"]]["mape"]
            for fold in candidate["folds"]
        ))
    selected = min(candidates, key=lambda value: (value["pooled"]["mape"], value["pooled"]["wape"]))
    improves_mape = selected["pooled"]["mape"] < baseline_metrics["mape"]
    status = "awaiting_independent_test_and_approval" if improves_mape else "no_improvement_keep_current_model"
    result = {
        "status": status,
        "selection_basis": "minimum pooled rolling MAPE with WAPE as tie breaker",
        "evaluation_seed": evaluation_seed,
        "test_used_for_selection": False,
        "baseline": {"candidate": "current_catboost_with_tsss", "pooled": baseline_metrics, "folds": baseline_folds},
        "candidates": candidates,
        "selected_candidate": selected["candidate"],
        "selected_pooled": selected["pooled"],
        "selected_mape_delta_vs_baseline": float(selected["pooled"]["mape"] - baseline_metrics["mape"]),
        "selected_wape_delta_vs_baseline": float(selected["pooled"]["wape"] - baseline_metrics["wape"]),
        "model_promoted": False,
        "reused_test_evaluated": False,
    }
    write_json(ROOT / "artifacts/enhanced_mape_benchmark.json", result)
    all_predictions = pd.concat(predictions, ignore_index=True)
    compression = {"method": "gzip", "compresslevel": 6, "mtime": 0}
    all_predictions.to_json(ROOT / "artifacts/enhanced_mape_oof_predictions.jsonl.gz", orient="records", lines=True, compression=compression, force_ascii=False, double_precision=15)
    print(json.dumps(result, ensure_ascii=False))
