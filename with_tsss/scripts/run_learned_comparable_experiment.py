from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from property_price_forecasting_tsss.modeling import regression_metrics
from property_price_forecasting_tsss.retrieval_adjustment import candidate_pool_features, fit_pair_models, fit_pair_models_full, predict_adjusted_three


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def fold_masks(dataframe, fold):
    dates = pd.to_datetime(dataframe["as_of_date"], format="%Y-%m-%d")
    return dates.between(fold["train_start"], fold["train_end"]), dates.between(fold["validation_start"], fold["validation_end"])


def evaluate_fold(data, pairs, fold, config, seed):
    train_mask, validation_mask = fold_masks(data, fold)
    train_rows = set(data.index[train_mask].tolist())
    validation_rows = set(data.index[validation_mask].tolist())
    train_pairs = pairs.loc[pairs["row_index"].isin(train_rows)].copy()
    validation_pairs = pairs.loc[pairs["row_index"].isin(validation_rows)].copy()
    selection, adjustment, selection_iterations, adjustment_iterations = fit_pair_models(train_pairs, validation_pairs, config, seed)
    predictions = predict_adjusted_three(validation_pairs, selection, adjustment, config)
    validation = data.loc[list(validation_rows), ["target_price_vnd_m2"]].rename(columns={"target_price_vnd_m2": "target"}).reset_index(names="row_index")
    frame = validation.merge(predictions, on="row_index", how="left")
    fallback = float(data.loc[train_mask, "target_price_vnd_m2"].median())
    frame["retrieval_prediction"] = frame["retrieval_prediction"].fillna(fallback)
    return frame, {"fold": fold["name"], "train_target_rows": int(len(train_rows)), "validation_target_rows": int(len(validation_rows)), "train_pair_rows": int(len(train_pairs)), "validation_pair_rows": int(len(validation_pairs)), "selection_iterations": selection_iterations, "adjustment_iterations": adjustment_iterations, "retrieval_metrics": regression_metrics(frame["target"], frame["retrieval_prediction"])}


if __name__ == "__main__":
    config = json.loads((ROOT / "configs/pipeline.json").read_text(encoding="utf-8"))
    split_manifest = json.loads((ROOT / config["base_split_file"]).resolve().read_text(encoding="utf-8"))
    base = pd.read_json((ROOT / config["base_cleaned_file"]).resolve(), lines=True, compression="gzip")
    source = pd.read_excel((ROOT / config["source_file"]).resolve(), sheet_name=config["source_sheet"])
    pairs, pair_manifest = candidate_pool_features(base, source, config)
    folds = split_manifest["folds"]
    oof_frames = []
    fold_results = []
    for fold_index, fold in enumerate(folds):
        frame, result = evaluate_fold(base, pairs, fold, config, int(config["random_seed"]) + fold_index * 10)
        frame["fold"] = fold["name"]
        oof_frames.append(frame)
        fold_results.append(result)
        print(json.dumps({"fold": fold["name"], "retrieval_mae": result["retrieval_metrics"]["mae_vnd_m2"]}, ensure_ascii=False))
    retrieval_oof = pd.concat(oof_frames, ignore_index=True).sort_values("row_index").reset_index(drop=True)
    baseline_oof = pd.read_json(ROOT / "artifacts/oof_predictions.jsonl.gz", lines=True, compression="gzip")[["row_index", "prediction"]].rename(columns={"prediction": "baseline_prediction"})
    oof = retrieval_oof.merge(baseline_oof, on="row_index", how="inner", validate="one_to_one")
    variants = {}
    for retrieval_weight in config["learned_comparable"]["retrieval_blend_weights"]:
        name = f"blend_retrieval_{retrieval_weight:.2f}"
        prediction = retrieval_weight * oof["retrieval_prediction"] + (1.0 - retrieval_weight) * oof["baseline_prediction"]
        variants[name] = regression_metrics(oof["target"], prediction)
        oof[name] = prediction
    selected_name = min(variants, key=lambda name: (variants[name]["mae_vnd_m2"], variants[name]["wape"]))
    selected_weight = float(selected_name.rsplit("_", 1)[1])
    development = base.loc[base["split"].eq("development")]
    test = base.loc[base["split"].eq("test")]
    development_pairs = pairs.loc[pairs["row_index"].isin(development.index)].copy()
    test_pairs = pairs.loc[pairs["row_index"].isin(test.index)].copy()
    selection_iterations = int(np.median([value["selection_iterations"] for value in fold_results]))
    adjustment_iterations = int(np.median([value["adjustment_iterations"] for value in fold_results]))
    selection, adjustment = fit_pair_models_full(development_pairs, config, int(config["random_seed"]), selection_iterations, adjustment_iterations)
    retrieval_test = predict_adjusted_three(test_pairs, selection, adjustment, config)
    test_frame = test[["target_price_vnd_m2"]].rename(columns={"target_price_vnd_m2": "target"}).reset_index(names="row_index").merge(retrieval_test, on="row_index", how="left")
    fallback = float(development["target_price_vnd_m2"].median())
    test_frame["retrieval_prediction"] = test_frame["retrieval_prediction"].fillna(fallback)
    baseline_test = pd.read_json(ROOT / "artifacts/reused_test_predictions.jsonl.gz", lines=True, compression="gzip")[["row_index", "prediction"]].rename(columns={"prediction": "baseline_prediction"})
    test_frame = test_frame.merge(baseline_test, on="row_index", how="inner", validate="one_to_one")
    test_variants = {}
    for retrieval_weight in config["learned_comparable"]["retrieval_blend_weights"]:
        name = f"blend_retrieval_{retrieval_weight:.2f}"
        test_frame[name] = retrieval_weight * test_frame["retrieval_prediction"] + (1.0 - retrieval_weight) * test_frame["baseline_prediction"]
        test_variants[name] = regression_metrics(test_frame["target"], test_frame[name])
    result = {
        "experiment": "learned_three_comparable_retrieval_adjustment",
        "test_used_for_selection": False,
        "base_model_changed": False,
        "pair_manifest": pair_manifest,
        "folds": fold_results,
        "rolling_oof": {"rows": int(len(oof)), "retrieval_only": regression_metrics(oof["target"], oof["retrieval_prediction"]), "frozen_with_tsss": regression_metrics(oof["target"], oof["baseline_prediction"]), "blends": variants, "selected_blend": selected_name, "selected_retrieval_weight": selected_weight},
        "reused_test_non_confirmatory": {"rows": int(len(test_frame)), "retrieval_only": regression_metrics(test_frame["target"], test_frame["retrieval_prediction"]), "frozen_with_tsss": regression_metrics(test_frame["target"], test_frame["baseline_prediction"]), "blends": test_variants},
        "full_fit_iterations": {"selection": selection_iterations, "adjustment": adjustment_iterations},
        "leakage_policy": "TSSS availability and market dates are strictly earlier than each target date; pair models are fit only from target rows in the fold train partition; reused test is not used for selection.",
    }
    compression = {"method": "gzip", "compresslevel": 6, "mtime": 0}
    output = oof[["row_index", "fold", "target", "retrieval_prediction", "baseline_prediction", *variants.keys(), "comparable_count_selected", "mean_selection_score", "mean_adjustment_abs_pct", "same_road_share_selected", "mean_candidate_age_days"]].copy()
    output["absolute_percentage_error_retrieval"] = (output["retrieval_prediction"] - output["target"]).abs() / np.maximum(output["target"], 1.0)
    output[selected_name + "_absolute_percentage_error"] = (output[selected_name] - output["target"]).abs() / np.maximum(output["target"], 1.0)
    output.to_json(ROOT / "artifacts/learned_comparable_oof_predictions.jsonl.gz", orient="records", lines=True, compression=compression, force_ascii=False, double_precision=15)
    test_output = test_frame[["row_index", "target", "retrieval_prediction", "baseline_prediction", *test_variants.keys(), "comparable_count_selected", "mean_selection_score", "mean_adjustment_abs_pct", "same_road_share_selected", "mean_candidate_age_days"]].copy()
    test_output.to_json(ROOT / "artifacts/learned_comparable_reused_test_predictions.jsonl.gz", orient="records", lines=True, compression=compression, force_ascii=False, double_precision=15)
    write_json(ROOT / "artifacts/learned_comparable_experiment.json", result)
    print(json.dumps(result["rolling_oof"], ensure_ascii=False))
