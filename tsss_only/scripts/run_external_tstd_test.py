from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str((ROOT / "../without_tsss/src").resolve()))

from property_price_forecasting.cleaning import clean_tstd
from tsss_only.modeling import frame_for_catboost, regression_metrics


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    config = json.loads((ROOT / "configs/pipeline.json").read_text(encoding="utf-8"))
    stage2 = ROOT / "artifacts/stage_02"
    stage3 = ROOT / "artifacts/stage_03"
    contract = json.loads((stage2 / "data_contract.json").read_text(encoding="utf-8"))
    final = json.loads((stage3 / "final_results.json").read_text(encoding="utf-8"))
    if not final["selected_model"].startswith("catboost"):
        raise ValueError("External TSTĐ test hiện chỉ hỗ trợ model CatBoost được chọn")
    source = pd.read_excel((ROOT / config["source_file"]).resolve(), sheet_name=config["source_sheet"])
    tstd_config = {**config, "eligible_warehouse_class": "TSTĐ", "prediction_object": "TSTĐ"}
    tstd, removed_invalid = clean_tstd(source, tstd_config)
    test = tstd.loc[tstd["split"].eq("test")].copy()
    categorical = contract["categorical_features"]
    numeric = contract["numeric_features"]
    features = categorical + numeric
    model = CatBoostRegressor()
    model.load_model(ROOT / final["model_path"])
    raw_prediction = model.predict(Pool(frame_for_catboost(test, features, categorical), cat_features=categorical))
    prediction = np.maximum(np.expm1(raw_prediction), 1.0) if final["selected_model"] != "catboost_raw" else np.maximum(raw_prediction, 1.0)
    frame = pd.DataFrame({
        "source_excel_row": test["source_excel_row"].to_numpy(),
        "as_of_date": test["as_of_date"].to_numpy(),
        "target": test[contract["target"]].to_numpy(dtype=float),
        "prediction": prediction,
    })
    frame["error"] = frame["prediction"] - frame["target"]
    frame["absolute_error"] = frame["error"].abs()
    frame["absolute_percentage_error"] = frame["absolute_error"] / np.maximum(frame["target"], 1.0)
    frame.to_json(stage3 / "external_tstd_test_predictions.jsonl.gz", orient="records", lines=True, compression={"method": "gzip", "compresslevel": 6, "mtime": 0}, force_ascii=False, double_precision=15)
    result = {
        "population": "TSTĐ only",
        "rows": int(len(frame)),
        "date_min": frame["as_of_date"].min(),
        "date_max": frame["as_of_date"].max(),
        "tsss_training_rows": int(pd.read_json(stage2 / "cleaned_tsss.jsonl.gz", lines=True, compression="gzip")["split"].eq("development").sum()),
        "tstd_rows_used_for_training_or_selection": 0,
        "tstd_invalid_target_or_date_rows_removed": removed_invalid,
        "metrics": regression_metrics(frame["target"], frame["prediction"]),
        "interpretation": "external temporal test from a distinct TSTĐ population"
    }
    write_json(stage3 / "external_tstd_test_results.json", result)
    print(json.dumps(result, ensure_ascii=True))
