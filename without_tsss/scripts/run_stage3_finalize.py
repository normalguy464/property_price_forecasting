from pathlib import Path
from hashlib import sha256
import json
import platform
import statistics
import sys

import catboost
import joblib
import numpy as np
import optuna
import pandas as pd
import sklearn


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from property_price_forecasting.modeling import HierarchicalMedianRegressor, build_ridge_pipeline, file_sha256, fit_full_catboost, fit_predict_catboost, fit_predict_ridge, fold_masks, price_band, regression_metrics, segmented_metrics


artifact_stage2 = PROJECT_ROOT / "artifacts" / "stage_02"
artifact_stage3 = PROJECT_ROOT / "artifacts" / "stage_03"
model_dir = artifact_stage3 / "model"
config = json.loads((PROJECT_ROOT / "configs" / "stage3.json").read_text(encoding="utf-8"))
contract = json.loads((artifact_stage2 / "data_contract.json").read_text(encoding="utf-8"))
split_manifest = json.loads((artifact_stage2 / "split_manifest.json").read_text(encoding="utf-8"))
benchmark = json.loads((artifact_stage3 / "benchmark_metrics.json").read_text(encoding="utf-8"))
best = json.loads((artifact_stage3 / "best_params.json").read_text(encoding="utf-8"))
data = pd.read_json(artifact_stage2 / "cleaned_tstd.jsonl.gz", orient="records", lines=True, compression="gzip")
development = data.loc[data["split"].eq(config["development_split"])].copy()
categorical = contract["categorical_features"]
numeric = contract["numeric_features"]
features = categorical + numeric
target = contract["target"]
ridge_alpha = float(benchmark["best_ridge_variant"].split("_")[-1])
candidate_records = {"hierarchical_median": [], "ridge": [], "catboost_tuned": []}
catboost_iterations = []


def add_records(name, fold, train, validation, prediction):
    road_counts = train["road"].value_counts()
    train_assets = set(train["asset_group_id"])
    for (_, row), predicted in zip(validation.iterrows(), prediction):
        actual = float(row[target])
        road_count = int(road_counts.get(row["road"], 0))
        candidate_records[name].append(
            {
                "source_excel_row": int(row["source_excel_row"]),
                "as_of_date": row["as_of_date"],
                "fold": fold["name"],
                "target": actual,
                "prediction": float(predicted),
                "district": row["district"],
                "business_advantage": row["business_advantage"],
                "price_position": row["price_position"],
                "month": str(row["as_of_date"])[:7],
                "price_band": price_band(actual),
                "road_frequency": "rare_or_unseen" if road_count < 5 else "common",
                "asset_history": "seen_in_fold_train" if row["asset_group_id"] in train_assets else "new_in_fold",
            }
        )


for fold in split_manifest["folds"]:
    train_mask, validation_mask = fold_masks(development, fold)
    train = development.loc[train_mask].copy()
    validation = development.loc[validation_mask].copy()
    baseline = HierarchicalMedianRegressor(**config["hierarchical_baseline"])
    baseline.fit(train, train[target], fold["validation_start"])
    baseline_prediction = baseline.predict(validation)
    add_records("hierarchical_median", fold, train, validation, baseline_prediction)
    _, ridge_prediction = fit_predict_ridge(
        train,
        validation,
        target,
        categorical,
        numeric,
        ridge_alpha,
        config["one_hot_min_frequency"],
    )
    add_records("ridge", fold, train, validation, ridge_prediction)
    _, catboost_prediction, iteration = fit_predict_catboost(
        train,
        validation,
        target,
        features,
        categorical,
        best["parameters"],
        config["catboost_common"],
        config["random_seed"],
    )
    catboost_iterations.append(iteration)
    add_records("catboost_tuned", fold, train, validation, catboost_prediction)


candidate_metrics = {}
for name, records in candidate_records.items():
    frame = pd.DataFrame(records)
    candidate_metrics[name] = regression_metrics(frame["target"], frame["prediction"])
selected_name = min(candidate_metrics, key=lambda name: candidate_metrics[name][config["primary_metric"]])
selected_oof = pd.DataFrame(candidate_records[selected_name])
selected_oof["error"] = selected_oof["prediction"] - selected_oof["target"]
selected_oof["absolute_error"] = selected_oof["error"].abs()
selected_oof["absolute_percentage_error"] = selected_oof["absolute_error"] / selected_oof["target"].abs().clip(lower=1)
fold_metrics = []
for fold_name, frame in selected_oof.groupby("fold"):
    fold_metrics.append({"fold": fold_name, **regression_metrics(frame["target"], frame["prediction"])})
segment_columns = ["fold", "month", "district", "business_advantage", "price_position", "price_band", "road_frequency", "asset_history"]
segments = segmented_metrics(selected_oof, segment_columns)
rolling_output = {
    "selected_model": selected_name,
    "primary_metric": config["primary_metric"],
    "overall": candidate_metrics[selected_name],
    "folds": fold_metrics,
    "candidate_comparison": candidate_metrics,
    "catboost_best_iterations_by_fold": catboost_iterations,
    "validation_rows_pooled": int(len(selected_oof)),
    "test_rows_used": 0,
}
(artifact_stage3 / "rolling_metrics.json").write_text(json.dumps(rolling_output, ensure_ascii=False, indent=2), encoding="utf-8")
(artifact_stage3 / "segment_metrics.json").write_text(json.dumps({"selected_model": selected_name, "segments": segments, "test_rows_used": 0}, ensure_ascii=False, indent=2), encoding="utf-8")
compression = {"method": "gzip", "compresslevel": 6, "mtime": 0}
selected_oof.to_json(artifact_stage3 / "oof_predictions.jsonl.gz", orient="records", lines=True, compression=compression, force_ascii=False, double_precision=15)
feature_importance = []
transformed_importance = []
importance_type = "not_available"
if selected_name == "catboost_tuned":
    final_iterations = int(round(statistics.median(catboost_iterations)))
    model = fit_full_catboost(
        development,
        target,
        features,
        categorical,
        best["parameters"],
        config["catboost_common"],
        config["random_seed"],
        final_iterations,
    )
    model_path = model_dir / "catboost_model.cbm"
    model.save_model(model_path)
    values = model.get_feature_importance()
    feature_importance = [
        {"feature": name, "importance": float(value)}
        for name, value in sorted(zip(features, values), key=lambda item: item[1], reverse=True)
    ]
    importance_type = "PredictionValuesChange"
    selected_parameters = {**best["parameters"], "iterations": final_iterations}
elif selected_name == "ridge":
    final_iterations = None
    model = build_ridge_pipeline(categorical, numeric, ridge_alpha, config["one_hot_min_frequency"])
    model.fit(development[features], np.log1p(development[target].to_numpy(dtype=float)))
    model_path = model_dir / "ridge_model.joblib"
    joblib.dump(model, model_path)
    selected_parameters = {"alpha": ridge_alpha, "target_transform": "log1p"}
    names = model.named_steps["preprocessor"].get_feature_names_out()
    coefficients = model.named_steps["model"].coef_
    pairs = sorted(zip(names, coefficients), key=lambda item: abs(item[1]), reverse=True)
    transformed_importance = [
        {"transformed_feature": str(name), "coefficient": float(value), "absolute_coefficient": float(abs(value))}
        for name, value in pairs[:200]
    ]
    aggregated = {}
    ordered_features = sorted(features, key=len, reverse=True)
    for name, value in zip(names, coefficients):
        suffix = str(name).split("__", 1)[-1]
        original = next((feature for feature in ordered_features if suffix == feature or suffix.startswith(feature + "_")), suffix)
        item = aggregated.setdefault(original, {"absolute_importance": 0.0, "signed_sum": 0.0, "max_absolute_coefficient": 0.0})
        item["absolute_importance"] += float(abs(value))
        item["signed_sum"] += float(value)
        item["max_absolute_coefficient"] = max(item["max_absolute_coefficient"], float(abs(value)))
    feature_importance = [
        {"feature": name, **values}
        for name, values in sorted(aggregated.items(), key=lambda item: item[1]["absolute_importance"], reverse=True)
    ]
    importance_type = "ridge_absolute_standardized_coefficients"
else:
    final_iterations = None
    model = HierarchicalMedianRegressor(**config["hierarchical_baseline"])
    model.fit(development, development[target], "2025-05-01")
    model_path = model_dir / "hierarchical_median.joblib"
    joblib.dump(model, model_path)
    selected_parameters = config["hierarchical_baseline"]
(artifact_stage3 / "feature_importance.json").write_text(json.dumps({"selected_model": selected_name, "importance_type": importance_type, "features": feature_importance, "top_transformed_features": transformed_importance}, ensure_ascii=False, indent=2), encoding="utf-8")
selected_output = {
    "model": selected_name,
    "selection_rule": "lowest pooled rolling MAE on development",
    "primary_metric": config["primary_metric"],
    "rolling_metrics": candidate_metrics[selected_name],
    "candidate_comparison": candidate_metrics,
    "parameters": selected_parameters,
    "target_transform": config["catboost_common"]["target_transform"] if selected_name == "catboost_tuned" else selected_parameters.get("target_transform", "none"),
    "random_seed": config["random_seed"],
    "categorical_features": categorical,
    "numeric_features": numeric,
    "model_path": str(model_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
    "model_sha256": file_sha256(model_path),
    "development_rows": int(len(development)),
    "test_rows_used": 0,
}
(artifact_stage3 / "selected_model.json").write_text(json.dumps(selected_output, ensure_ascii=False, indent=2), encoding="utf-8")
runtime = {
    "python": platform.python_version(),
    "pandas": pd.__version__,
    "scikit_learn": sklearn.__version__,
    "catboost": catboost.__version__,
    "optuna": optuna.__version__,
}
(artifact_stage3 / "runtime_versions.json").write_text(json.dumps(runtime, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"selected_model={selected_name}")
print(f"rolling_mae={candidate_metrics[selected_name][config['primary_metric']]:.2f}")
print(f"model_path={model_path}")
