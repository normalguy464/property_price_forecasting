from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from property_price_forecasting_tsss.modeling import fit_predict_catboost, price_band, price_band_sample_weights, regression_metrics


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def metrics_with_mape(y_true, y_pred):
    metrics = regression_metrics(y_true, y_pred)
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    metrics["mape"] = float(np.mean(np.abs(y_pred - y_true) / np.maximum(np.abs(y_true), 1.0)))
    return metrics


def prediction_frame(data, indices, prediction, fold):
    source = data.loc[indices]
    frame = pd.DataFrame({"row_index": indices, "fold": fold, "prediction": prediction})
    frame["as_of_date"] = source["as_of_date"].to_numpy()
    frame["target"] = source["target_price_vnd_m2"].to_numpy(dtype=float)
    frame["district"] = source["district"].to_numpy()
    frame["price_position"] = source["price_position"].to_numpy()
    frame["business_advantage"] = source["business_advantage"].to_numpy()
    frame["price_band"] = [price_band(value) for value in frame["target"]]
    frame["error"] = frame["prediction"] - frame["target"]
    frame["absolute_error"] = frame["error"].abs()
    frame["absolute_percentage_error"] = frame["absolute_error"] / np.maximum(frame["target"], 1.0)
    return frame


def metrics_by_price_band(frame):
    return {
        str(band): metrics_with_mape(group["target"], group["prediction"])
        for band, group in frame.groupby("price_band", sort=True)
    }


if __name__ == "__main__":
    config = json.loads((ROOT / "configs/pipeline.json").read_text(encoding="utf-8"))
    contract = json.loads((ROOT / "../without_tsss/artifacts/stage_02/data_contract.json").resolve().read_text(encoding="utf-8"))
    feature_manifest = json.loads((ROOT / "artifacts/feature_manifest.json").read_text(encoding="utf-8"))
    split_manifest = json.loads((ROOT / config["base_split_file"]).resolve().read_text(encoding="utf-8"))
    model_manifest = json.loads((ROOT / "artifacts/model_manifest.json").read_text(encoding="utf-8"))
    base = pd.read_json((ROOT / config["base_cleaned_file"]).resolve(), lines=True, compression="gzip")
    market = pd.read_json(ROOT / "artifacts/market_features.jsonl.gz", lines=True, compression="gzip")
    data = pd.concat([base.reset_index(drop=True), market.drop(columns=["source_excel_row"]).reset_index(drop=True)], axis=1)
    categorical = contract["categorical_features"]
    features = categorical + contract["numeric_features"] + feature_manifest["market_features"]
    parameters = model_manifest["parameters"]
    weighting_config = config["rare_price_band_weighting"]
    dates = pd.to_datetime(data["as_of_date"], format="%Y-%m-%d")
    parts = []
    fold_details = []
    for fold_index, fold in enumerate(split_manifest["folds"]):
        train = data.loc[dates.between(fold["train_start"], fold["train_end"])]
        validation = data.loc[dates.between(fold["validation_start"], fold["validation_end"])]
        weights, weight_manifest = price_band_sample_weights(train["target_price_vnd_m2"], weighting_config["max_weight"])
        _, prediction, best_iteration = fit_predict_catboost(
            train,
            validation,
            "target_price_vnd_m2",
            features,
            categorical,
            parameters,
            config["random_seed"] + fold_index,
            sample_weight=weights,
        )
        frame = prediction_frame(data, validation.index.to_numpy(), prediction, fold["name"])
        parts.append(frame)
        fold_details.append({
            "fold": fold["name"],
            "train_rows": int(len(train)),
            "validation_rows": int(len(validation)),
            "best_iteration": best_iteration,
            "weights": weight_manifest,
            "metrics": metrics_with_mape(frame["target"], frame["prediction"]),
        })
    weighted_oof = pd.concat(parts, ignore_index=True)
    baseline_oof = pd.read_json(ROOT / "artifacts/oof_predictions.jsonl.gz", lines=True, compression="gzip")
    if set(weighted_oof["row_index"]) != set(baseline_oof["row_index"]):
        raise ValueError("OOF weighted và baseline không cùng tập validation")
    weighted_metrics = metrics_with_mape(weighted_oof["target"], weighted_oof["prediction"])
    baseline_metrics = metrics_with_mape(baseline_oof["target"], baseline_oof["prediction"])
    weighted_by_price_band = metrics_by_price_band(weighted_oof)
    baseline_by_price_band = metrics_by_price_band(baseline_oof)
    compression = {"method": "gzip", "compresslevel": 6, "mtime": 0}
    weighted_oof.to_json(ROOT / "artifacts/weighted_training_oof_predictions.jsonl.gz", orient="records", lines=True, compression=compression, force_ascii=False, double_precision=15)
    result = {
        "status": "experiment_only_not_promoted",
        "model": "catboost_with_tsss_tuned",
        "model_parameters": parameters,
        "weighting": {
            **weighting_config,
            "fit_scope": "training_rows_of_each_rolling_fold_only",
            "validation_weighting": "none",
            "oversampling": False,
        },
        "baseline_metrics": baseline_metrics,
        "weighted_metrics": weighted_metrics,
        "delta_weighted_minus_baseline": {name: float(weighted_metrics[name] - baseline_metrics[name]) for name in weighted_metrics},
        "baseline_metrics_by_price_band": baseline_by_price_band,
        "weighted_metrics_by_price_band": weighted_by_price_band,
        "mape_delta_by_price_band": {
            band: float(weighted_by_price_band[band]["mape"] - baseline_by_price_band[band]["mape"])
            for band in weighted_by_price_band
        },
        "folds": fold_details,
        "oof_rows": int(len(weighted_oof)),
        "test_used": False,
    }
    write_json(ROOT / "artifacts/weighted_training_experiment.json", result)
    print(json.dumps(result, ensure_ascii=False))
