from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from property_price_forecasting_wape.experiments import ANCHOR_FEATURES, add_anchor_features, fit_variant, metrics, write_json


VARIANTS = ["direct_history", "residual_market", "residual_hybrid"]


def masks(dataframe, fold):
    dates = pd.to_datetime(dataframe["as_of_date"], format="%Y-%m-%d")
    return dates.between(fold["train_start"], fold["train_end"]), dates.between(fold["validation_start"], fold["validation_end"])


def candidate(name, target, prediction, details=None):
    return {"name": name, "metrics": metrics(target, prediction), "details": {} if details is None else details}


if __name__ == "__main__":
    config = json.loads((ROOT / "configs/experiments.json").read_text(encoding="utf-8"))
    contract = json.loads((ROOT / config["base_contract_file"]).resolve().read_text(encoding="utf-8"))
    split = json.loads((ROOT / config["split_file"]).resolve().read_text(encoding="utf-8"))
    market_manifest = json.loads((ROOT / config["with_tsss_feature_manifest_file"]).resolve().read_text(encoding="utf-8"))
    history_manifest = json.loads((ROOT / "artifacts/history_manifest.json").read_text(encoding="utf-8"))
    base = pd.read_json((ROOT / config["base_cleaned_file"]).resolve(), lines=True, compression="gzip")
    market = pd.read_json((ROOT / config["with_tsss_feature_file"]).resolve(), lines=True, compression="gzip")
    history = pd.read_json(ROOT / "artifacts/history_features.jsonl.gz", lines=True, compression="gzip")
    if not base["source_excel_row"].equals(market["source_excel_row"]) or not base["source_excel_row"].equals(history["source_excel_row"]):
        raise RuntimeError("Input feature alignment failed")
    data = pd.concat([base, market.drop(columns=["source_excel_row"]), history.drop(columns=["source_excel_row"])], axis=1)
    data = add_anchor_features(data)
    categorical = contract["categorical_features"]
    numeric = contract["numeric_features"] + market_manifest["market_features"] + history_manifest["features"] + ANCHOR_FEATURES
    features = categorical + numeric
    current = pd.read_json((ROOT / config["with_tsss_oof_file"]).resolve(), lines=True, compression="gzip")
    current = current.sort_values("row_index").reset_index(drop=True)
    oof_indices = current["row_index"].to_numpy(dtype=int)
    target = data.loc[oof_indices, "target_price_vnd_m2"].to_numpy(dtype=float)
    predictions = {"with_tsss_frozen": current["prediction"].to_numpy(dtype=float)}
    fold_iterations = {}
    for variant_index, variant in enumerate(VARIANTS):
        records = []
        iterations = []
        for fold_index, fold in enumerate(split["folds"]):
            train_mask, validation_mask = masks(data, fold)
            train = data.loc[train_mask]
            validation = data.loc[validation_mask]
            _, prediction, best_iteration = fit_variant(train, validation, "target_price_vnd_m2", features, categorical, config["catboost"], config["random_seed"] + variant_index * 20 + fold_index, variant)
            iterations.append(best_iteration)
            records.extend(zip(validation.index.to_numpy(dtype=int), prediction.tolist()))
            print(json.dumps({"variant": variant, "fold": fold["name"], "best_iteration": best_iteration, "mae": metrics(validation["target_price_vnd_m2"], prediction)["mae_vnd_m2"]}))
        frame = pd.DataFrame(records, columns=["row_index", "prediction"]).sort_values("row_index")
        if not np.array_equal(frame["row_index"].to_numpy(dtype=int), oof_indices):
            raise RuntimeError(f"OOF alignment failed: {variant}")
        predictions[variant] = frame["prediction"].to_numpy(dtype=float)
        fold_iterations[variant] = iterations
    candidates = [candidate(name, target, values, {"kind": "single"}) for name, values in predictions.items()]
    for left, right in [("with_tsss_frozen", "direct_history"), ("with_tsss_frozen", "residual_market"), ("with_tsss_frozen", "residual_hybrid"), ("direct_history", "residual_hybrid")]:
        for right_weight in config["blend_weights"]:
            name = f"blend_{left}_{right}_right_{right_weight}"
            values = predictions[left] * (1 - right_weight) + predictions[right] * right_weight
            predictions[name] = values
            candidates.append(candidate(name, target, values, {"kind": "blend", "left": left, "right": right, "right_weight": right_weight}))
    triple_name = "blend_equal_current_direct_hybrid"
    predictions[triple_name] = (predictions["with_tsss_frozen"] + predictions["direct_history"] + predictions["residual_hybrid"]) / 3
    candidates.append(candidate(triple_name, target, predictions[triple_name], {"kind": "equal_three"}))
    calibrated = []
    base_candidates = sorted(candidates, key=lambda value: value["metrics"]["mae_vnd_m2"])[:5]
    factors = [0.98, 0.99, 1.0, 1.01, 1.02, 1.03, 1.04]
    for item in base_candidates:
        for factor in factors:
            name = f"calibrated_{item['name']}_{factor}"
            values = predictions[item["name"]] * factor
            predictions[name] = values
            calibrated.append(candidate(name, target, values, {"kind": "global_factor", "base": item["name"], "factor": factor}))
    candidates.extend(calibrated)
    selected = min(candidates, key=lambda value: value["metrics"]["mae_vnd_m2"])
    selected_predictions = predictions[selected["name"]]
    oof = pd.DataFrame({
        "row_index": oof_indices,
        "as_of_date": data.loc[oof_indices, "as_of_date"].to_numpy(),
        "target": target,
        "prediction": selected_predictions,
        "district": data.loc[oof_indices, "district"].to_numpy(),
        "business_advantage": data.loc[oof_indices, "business_advantage"].to_numpy(),
        "price_position": data.loc[oof_indices, "price_position"].to_numpy(),
        "market_road_count_365d": data.loc[oof_indices, "market_road_count_365d"].to_numpy(dtype=float),
        "history_road_count_365d": data.loc[oof_indices, "history_road_count_365d"].to_numpy(dtype=float),
    })
    oof["error"] = oof["prediction"] - oof["target"]
    oof["absolute_error"] = oof["error"].abs()
    oof["absolute_percentage_error"] = oof["absolute_error"] / np.maximum(oof["target"], 1.0)
    compression = {"method": "gzip", "compresslevel": 6, "mtime": 0}
    oof.to_json(ROOT / "artifacts/selected_oof_predictions.jsonl.gz", orient="records", lines=True, compression=compression, force_ascii=False, double_precision=15)
    np.savez_compressed(ROOT / "artifacts/component_oof_predictions.npz", row_index=oof_indices, **{name: values for name, values in predictions.items() if name in ["with_tsss_frozen", *VARIANTS]})
    result = {
        "selection_population": "rolling_oof_development_only",
        "test_used_for_selection": False,
        "target_wape": config["target_wape"],
        "target_reached": selected["metrics"]["wape"] < config["target_wape"],
        "selected": selected,
        "single_models": [value for value in candidates if value["details"].get("kind") == "single"],
        "top_candidates": sorted(candidates, key=lambda value: value["metrics"]["mae_vnd_m2"])[:20],
        "fold_iterations": fold_iterations,
        "feature_count": len(features),
        "categorical_features": categorical,
        "numeric_features": numeric,
    }
    write_json(ROOT / "artifacts/experiment_results.json", result)
    print(json.dumps({"selected": selected, "target_reached": result["target_reached"]}, ensure_ascii=False))
