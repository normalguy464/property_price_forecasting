from pathlib import Path
import json
import sys

import numpy as np
import optuna
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from property_price_forecasting_tsss.modeling import fit_predict_catboost, regression_metrics


def fold_masks(dataframe, fold):
    dates = pd.to_datetime(dataframe["as_of_date"], format="%Y-%m-%d")
    return dates.between(fold["train_start"], fold["train_end"]), dates.between(fold["validation_start"], fold["validation_end"])


def objective_factory(data, folds, categorical, numeric, base_config, seed):
    features = categorical + numeric

    def objective(trial):
        parameters = {
            **base_config,
            "iterations": 800,
            "depth": trial.suggest_int("depth", 4, 7),
            "learning_rate": trial.suggest_float("learning_rate", 0.04, 0.24, log=True),
            "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 3.0, 30.0, log=True),
            "random_strength": trial.suggest_float("random_strength", 0.1, 3.0, log=True),
            "bagging_temperature": trial.suggest_float("bagging_temperature", 0.2, 3.0),
            "border_count": trial.suggest_categorical("border_count", [128, 254]),
        }
        targets = []
        predictions = []
        best_iterations = []
        fold_mae = []
        for fold_index, fold in enumerate(folds):
            train_mask, validation_mask = fold_masks(data, fold)
            train = data.loc[train_mask]
            validation = data.loc[validation_mask]
            _, prediction, best_iteration = fit_predict_catboost(train, validation, "target_price_vnd_m2", features, categorical, parameters, seed + trial.number * 10 + fold_index)
            target = validation["target_price_vnd_m2"].to_numpy(dtype=float)
            targets.extend(target.tolist())
            predictions.extend(prediction.tolist())
            best_iterations.append(best_iteration)
            fold_mae.append(regression_metrics(target, prediction)["mae_vnd_m2"])
        metrics = regression_metrics(targets, predictions)
        trial.set_user_attr("fold_mae", fold_mae)
        trial.set_user_attr("best_iterations", best_iterations)
        trial.set_user_attr("pooled_metrics", metrics)
        return metrics["mae_vnd_m2"]

    return objective


if __name__ == "__main__":
    config = json.loads((ROOT / "configs/pipeline.json").read_text(encoding="utf-8"))
    contract = json.loads((ROOT / "../without_tsss/artifacts/stage_02/data_contract.json").resolve().read_text(encoding="utf-8"))
    feature_manifest = json.loads((ROOT / "artifacts/feature_manifest.json").read_text(encoding="utf-8"))
    split_manifest = json.loads((ROOT / config["base_split_file"]).resolve().read_text(encoding="utf-8"))
    base = pd.read_json((ROOT / config["base_cleaned_file"]).resolve(), lines=True, compression="gzip")
    market = pd.read_json(ROOT / "artifacts/market_features.jsonl.gz", lines=True, compression="gzip")
    data = pd.concat([base.reset_index(drop=True), market.drop(columns=["source_excel_row"]).reset_index(drop=True)], axis=1)
    categorical = contract["categorical_features"]
    numeric = contract["numeric_features"] + feature_manifest["market_features"]
    storage = f"sqlite:///{(ROOT / 'artifacts/optuna_study.db').as_posix()}"
    sampler = optuna.samplers.TPESampler(seed=config["random_seed"], n_startup_trials=2)
    study = optuna.create_study(study_name="catboost_with_tsss_rolling", storage=storage, direction="minimize", sampler=sampler, load_if_exists=True)
    if len(study.trials) == 0:
        current = config["catboost"]
        study.enqueue_trial({name: current[name] for name in ["depth", "learning_rate", "l2_leaf_reg", "random_strength", "bagging_temperature", "border_count"]})
    remaining = max(0, 6 - len(study.trials))
    if remaining:
        study.optimize(objective_factory(data, split_manifest["folds"], categorical, numeric, config["catboost"], config["random_seed"]), n_trials=remaining)
    trials = []
    for trial in study.trials:
        trials.append({"number": trial.number, "state": trial.state.name, "value": trial.value, "parameters": trial.params, "user_attributes": trial.user_attrs})
    best = {"number": study.best_trial.number, "value": study.best_value, "parameters": study.best_trial.params, "user_attributes": study.best_trial.user_attrs}
    (ROOT / "artifacts/tuning_trials.json").write_text(json.dumps(trials, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "artifacts/best_parameters.json").write_text(json.dumps(best, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(best, ensure_ascii=False))
