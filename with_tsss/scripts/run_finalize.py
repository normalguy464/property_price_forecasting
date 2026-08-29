from pathlib import Path
import json
import sys

import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from property_price_forecasting_tsss.modeling import catboost_parameters, file_sha256, fit_predict_catboost, frame_for_catboost, price_band, regression_metrics, segment_metrics


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def enrich(data, indices, predictions, fold):
    source = data.loc[indices]
    frame = pd.DataFrame({"row_index": indices, "fold": fold, "prediction": predictions})
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
    best = json.loads((ROOT / "artifacts/best_parameters.json").read_text(encoding="utf-8"))
    benchmark = json.loads((ROOT / "artifacts/benchmark_results.json").read_text(encoding="utf-8"))
    base = pd.read_json((ROOT / config["base_cleaned_file"]).resolve(), lines=True, compression="gzip")
    market = pd.read_json(ROOT / "artifacts/market_features.jsonl.gz", lines=True, compression="gzip")
    data = pd.concat([base.reset_index(drop=True), market.drop(columns=["source_excel_row"]).reset_index(drop=True)], axis=1)
    categorical = contract["categorical_features"]
    numeric = contract["numeric_features"] + feature_manifest["market_features"]
    features = categorical + numeric
    fixed_candidate = next(value for value in benchmark["candidates"] if value["variant"] == "catboost_with_tsss")
    tuning_wins = best["value"] < fixed_candidate["pooled"]["mae_vnd_m2"]
    selected_parameters = {**config["catboost"], **best["parameters"]} if tuning_wins else config["catboost"]
    selected_iterations = int(np.median(best["user_attributes"]["best_iterations"])) if tuning_wins else int(np.median(fixed_candidate["best_iterations"]))
    development = data.loc[data["split"].eq("development")]
    test = data.loc[data["split"].eq("test")]
    oof_parts = []
    evaluation_parameters = {**selected_parameters, "iterations": 800 if tuning_wins else selected_parameters["iterations"]}
    dates = pd.to_datetime(data["as_of_date"], format="%Y-%m-%d")
    for fold_index, fold in enumerate(split_manifest["folds"]):
        train = data.loc[dates.between(fold["train_start"], fold["train_end"])]
        validation = data.loc[dates.between(fold["validation_start"], fold["validation_end"])]
        seed = config["random_seed"] + (best["number"] * 10 if tuning_wins else 0) + fold_index
        _, prediction, _ = fit_predict_catboost(train, validation, "target_price_vnd_m2", features, categorical, evaluation_parameters, seed)
        fold_frame = enrich(data, validation.index.to_numpy(), prediction, fold["name"])
        seen_assets = set(train["asset_group_id"])
        fold_frame["asset_history"] = np.where(validation["asset_group_id"].isin(seen_assets).to_numpy(), "seen_asset", "new_asset")
        oof_parts.append(fold_frame)
    oof = pd.concat(oof_parts, ignore_index=True)
    rolling_metrics = regression_metrics(oof["target"], oof["prediction"])
    oof.to_json(ROOT / "artifacts/oof_predictions.jsonl.gz", orient="records", lines=True, compression={"method": "gzip", "compresslevel": 6, "mtime": 0}, force_ascii=False, double_precision=15)
    write_json(ROOT / "artifacts/oof_segment_metrics.json", segment_metrics(oof, ["month", "district", "business_advantage", "price_position", "asset_history", "price_band", "market_road_coverage", "comparable_coverage"]))
    effective_parameters = {**selected_parameters, "iterations": selected_iterations}
    parameters = catboost_parameters(effective_parameters, config["random_seed"])
    model = CatBoostRegressor(**parameters)
    train_pool = Pool(frame_for_catboost(development, features, categorical), label=np.log1p(development["target_price_vnd_m2"].to_numpy(dtype=float)), cat_features=categorical)
    model.fit(train_pool)
    test_pool = Pool(frame_for_catboost(test, features, categorical), cat_features=categorical)
    test_prediction = np.maximum(np.expm1(model.predict(test_pool)), 1.0)
    model_path = ROOT / "artifacts/model.cbm"
    model.save_model(model_path)
    test_frame = enrich(data, test.index.to_numpy(), test_prediction, "reused_test")
    compression = {"method": "gzip", "compresslevel": 6, "mtime": 0}
    test_frame.to_json(ROOT / "artifacts/reused_test_predictions.jsonl.gz", orient="records", lines=True, compression=compression, force_ascii=False, double_precision=15)
    segments = segment_metrics(test_frame, ["month", "district", "business_advantage", "price_position", "asset_history", "price_band", "market_road_coverage", "comparable_coverage"])
    write_json(ROOT / "artifacts/test_segment_metrics.json", segments)
    old_test_metrics = json.loads((ROOT / config["old_test_metrics_file"]).resolve().read_text(encoding="utf-8"))["overall"]
    final = {
        "selection_basis": "pooled rolling MAE only",
        "test_used_for_selection": False,
        "selected": "catboost_with_tsss_tuned" if tuning_wins else "catboost_with_tsss_fixed",
        "rolling_metrics": rolling_metrics,
        "parameters": effective_parameters,
        "iterations": selected_iterations,
        "reused_test_non_confirmatory": {
            "with_tsss": regression_metrics(test_frame["target"], test_frame["prediction"]),
            "without_tsss_frozen": old_test_metrics,
        },
    }
    write_json(ROOT / "artifacts/final_results.json", final)
    manifest = {
        "model_type": "catboost",
        "model_path": "artifacts/model.cbm",
        "model_sha256": file_sha256(model_path),
        "selected": final["selected"],
        "parameters": effective_parameters,
        "iterations": selected_iterations,
        "categorical_features": categorical,
        "base_numeric_features": contract["numeric_features"],
        "market_numeric_features": feature_manifest["market_features"],
        "development_rows": int(len(development)),
        "test_rows": int(len(test)),
        "tsss_used_as_target_rows": 0,
        "tsss_used_as_historical_feature_source": True,
        "test_is_reused_non_confirmatory": True,
    }
    write_json(ROOT / "artifacts/model_manifest.json", manifest)
    print(json.dumps(final, ensure_ascii=False))
