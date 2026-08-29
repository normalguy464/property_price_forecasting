from pathlib import Path
import json
import statistics
import sys

import optuna
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from property_price_forecasting.modeling import fit_predict_catboost, fold_masks, regression_metrics


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
optuna.logging.set_verbosity(optuna.logging.WARNING)


def objective(trial):
    parameters = {
        "iterations": config["optuna"]["max_iterations"],
        "depth": trial.suggest_int("depth", 4, 7),
        "learning_rate": trial.suggest_float("learning_rate", 0.03, 0.20, log=True),
        "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1.0, 30.0, log=True),
        "random_strength": trial.suggest_float("random_strength", 0.05, 5.0, log=True),
        "bagging_temperature": trial.suggest_float("bagging_temperature", 0.0, 5.0),
        "border_count": trial.suggest_categorical("border_count", [64, 128, 254]),
    }
    fold_mae = []
    best_iterations = []
    for step, fold in enumerate(split_manifest["folds"]):
        train_mask, validation_mask = fold_masks(development, fold)
        train = development.loc[train_mask].copy()
        validation = development.loc[validation_mask].copy()
        _, prediction, iteration = fit_predict_catboost(
            train,
            validation,
            target,
            features,
            categorical,
            parameters,
            config["catboost_common"],
            config["random_seed"],
        )
        mae = regression_metrics(validation[target], prediction)[config["primary_metric"]]
        fold_mae.append(mae)
        best_iterations.append(iteration)
        weighted = sum(value * split_manifest["folds"][index]["validation_rows"] for index, value in enumerate(fold_mae))
        rows = sum(split_manifest["folds"][index]["validation_rows"] for index in range(len(fold_mae)))
        trial.report(weighted / rows, step)
        if trial.should_prune():
            trial.set_user_attr("fold_mae", fold_mae)
            trial.set_user_attr("best_iterations", best_iterations)
            raise optuna.TrialPruned()
    trial.set_user_attr("fold_mae", fold_mae)
    trial.set_user_attr("best_iterations", best_iterations)
    weighted = sum(value * fold["validation_rows"] for value, fold in zip(fold_mae, split_manifest["folds"]))
    return weighted / sum(fold["validation_rows"] for fold in split_manifest["folds"])


database_path = artifact_stage3 / "optuna_study.db"
storage = f"sqlite:///{database_path.as_posix()}"
existing_trials = 0
if database_path.exists():
    try:
        existing_study = optuna.load_study(study_name=config["optuna"]["study_name"], storage=storage)
        existing_trials = len(existing_study.trials)
    except KeyError:
        existing_trials = 0
sampler = optuna.samplers.TPESampler(seed=config["random_seed"] + existing_trials * 997)
pruner = optuna.pruners.MedianPruner(
    n_startup_trials=config["optuna"]["startup_trials"],
    n_warmup_steps=config["optuna"]["warmup_folds"],
)
study = optuna.create_study(
    study_name=config["optuna"]["study_name"],
    direction="minimize",
    sampler=sampler,
    pruner=pruner,
    storage=storage,
    load_if_exists=True,
)


def report_progress(study, trial):
    value = "none" if trial.value is None else f"{trial.value:.2f}"
    print(f"trial={trial.number} state={trial.state.name} value={value} best={study.best_value:.2f}", flush=True)


remaining = max(0, config["optuna"]["total_trials"] - len(study.trials))
if remaining:
    study.optimize(objective, n_trials=remaining, gc_after_trial=True, callbacks=[report_progress])
best = study.best_trial
best_parameters = {
    "iterations": config["optuna"]["max_iterations"],
    **best.params,
}
best_iterations = best.user_attrs["best_iterations"]
best_output = {
    "study_name": config["optuna"]["study_name"],
    "primary_metric": config["primary_metric"],
    "objective_value": float(best.value),
    "trial_number": int(best.number),
    "parameters": best_parameters,
    "fold_mae": best.user_attrs["fold_mae"],
    "best_iterations_by_fold": best_iterations,
    "recommended_full_iterations": int(round(statistics.median(best_iterations))),
    "test_rows_used": 0,
    "target_effective_configurations": config["optuna"]["target_effective_configurations"],
}
trials = []
for trial in study.trials:
    trials.append(
        {
            "number": int(trial.number),
            "state": trial.state.name,
            "value": None if trial.value is None else float(trial.value),
            "parameters": trial.params,
            "fold_mae": trial.user_attrs.get("fold_mae", []),
            "best_iterations": trial.user_attrs.get("best_iterations", []),
        }
    )
(artifact_stage3 / "best_params.json").write_text(json.dumps(best_output, ensure_ascii=False, indent=2), encoding="utf-8")
(artifact_stage3 / "optuna_trials.json").write_text(json.dumps({"total_trials": len(trials), "trials": trials}, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"trials={len(trials)}")
print(f"best_trial={best.number}")
print(f"best_mae={best.value:.2f}")
print(f"recommended_iterations={best_output['recommended_full_iterations']}")
