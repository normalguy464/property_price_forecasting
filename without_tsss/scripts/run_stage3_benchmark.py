from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from property_price_forecasting.modeling import HierarchicalMedianRegressor, fit_predict_catboost, fit_predict_ridge, fold_masks, pooled_metrics, regression_metrics


artifact_stage2 = PROJECT_ROOT / "artifacts" / "stage_02"
artifact_stage3 = PROJECT_ROOT / "artifacts" / "stage_03"
config = json.loads((PROJECT_ROOT / "configs" / "stage3.json").read_text(encoding="utf-8"))
contract = json.loads((artifact_stage2 / "data_contract.json").read_text(encoding="utf-8"))
split_manifest = json.loads((artifact_stage2 / "split_manifest.json").read_text(encoding="utf-8"))
data = pd.read_json(artifact_stage2 / "cleaned_tstd.jsonl.gz", orient="records", lines=True, compression="gzip")
development = data.loc[data["split"].eq(config["development_split"])].copy()
categorical = contract["categorical_features"]
numeric = contract["numeric_features"]
features = categorical + numeric
target = contract["target"]
records = {}
fold_results = {}
best_iterations = []

for fold in split_manifest["folds"]:
    train_mask, validation_mask = fold_masks(development, fold)
    train = development.loc[train_mask].copy()
    validation = development.loc[validation_mask].copy()
    baseline = HierarchicalMedianRegressor(**config["hierarchical_baseline"])
    baseline.fit(train, train[target], fold["validation_start"])
    baseline_prediction = baseline.predict(validation)
    variants = {"hierarchical_median": baseline_prediction}
    for alpha in config["ridge_alphas"]:
        name = f"ridge_alpha_{alpha:g}"
        _, prediction = fit_predict_ridge(train, validation, target, categorical, numeric, alpha, config["one_hot_min_frequency"])
        variants[name] = prediction
    _, catboost_prediction, iteration = fit_predict_catboost(
        train,
        validation,
        target,
        features,
        categorical,
        config["catboost_default"],
        config["catboost_common"],
        config["random_seed"],
    )
    variants["catboost_default"] = catboost_prediction
    best_iterations.append(iteration)
    for name, prediction in variants.items():
        fold_results.setdefault(name, []).append({"fold": fold["name"], **regression_metrics(validation[target], prediction)})
        records.setdefault(name, []).extend(
            {"target": float(actual), "prediction": float(predicted)}
            for actual, predicted in zip(validation[target], prediction)
        )

models = {}
for name in records:
    models[name] = {
        "folds": fold_results[name],
        "pooled": pooled_metrics(records[name]),
    }
ridge_names = [name for name in models if name.startswith("ridge_alpha_")]
best_ridge = min(ridge_names, key=lambda name: models[name]["pooled"][config["primary_metric"]])
winner = min(models, key=lambda name: models[name]["pooled"][config["primary_metric"]])
result = {
    "primary_metric": config["primary_metric"],
    "development_rows": int(len(development)),
    "validation_rows_pooled": int(sum(item["validation_rows"] for item in split_manifest["folds"])),
    "test_rows_used": 0,
    "models": models,
    "best_ridge_variant": best_ridge,
    "benchmark_winner": winner,
    "catboost_default_best_iterations": best_iterations,
    "catboost_default_parameters": config["catboost_default"],
}
(artifact_stage3 / "benchmark_metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"benchmark_winner={winner}")
print(f"benchmark_mae={models[winner]['pooled'][config['primary_metric']]:.2f}")
print(f"best_ridge={best_ridge}")
