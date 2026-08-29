from pathlib import Path
import json
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str((ROOT / "../without_tsss/src").resolve()))

from property_price_forecasting.cleaning import CATEGORICAL_FEATURES, DIAGNOSTIC_COLUMNS, LEAKAGE_SOURCE_COLUMNS, METADATA_COLUMNS, NUMERIC_FEATURES, SENSITIVE_SOURCE_COLUMNS, TARGET_COLUMNS, clean_tstd, output_file_sha256, source_file_sha256, write_clean_jsonl, write_json
from property_price_forecasting.splitting import build_split_manifest


if __name__ == "__main__":
    config = json.loads((ROOT / "configs/pipeline.json").read_text(encoding="utf-8"))
    output = ROOT / "artifacts/stage_02"
    source_path = (ROOT / config["source_file"]).resolve()
    source = pd.read_excel(source_path, sheet_name=config["source_sheet"])
    cleaned, removed_invalid = clean_tstd(source, config)
    clean_path = output / "cleaned_tsss.jsonl.gz"
    write_clean_jsonl(clean_path, cleaned)
    split = build_split_manifest(cleaned, config)
    split["population"] = "TSSS only"
    split["tsss_used"] = True
    write_json(output / "split_manifest.json", split)
    contract = {
        "version": "tsss-only-stage2-v1",
        "source_file": source_path.name,
        "source_sha256": source_file_sha256(source_path),
        "population": "TSSS only",
        "prediction_object": "TSSS",
        "prediction_time": config["as_of_column"],
        "target": "target_price_vnd_m2",
        "target_source_column": config["target_column"],
        "target_unit": config["target_unit"],
        "categorical_features": CATEGORICAL_FEATURES,
        "numeric_features": NUMERIC_FEATURES,
        "metadata_columns": METADATA_COLUMNS,
        "target_columns": TARGET_COLUMNS,
        "diagnostic_columns": DIAGNOSTIC_COLUMNS,
        "leakage_source_columns": LEAKAGE_SOURCE_COLUMNS,
        "sensitive_source_columns": SENSITIVE_SOURCE_COLUMNS,
        "excluded_source_columns": ["Tình trạng giao dịch"],
        "transaction_status_used_as_feature": False,
        "outlier_rows_removed": 0,
        "invalid_target_or_date_rows_removed": removed_invalid
    }
    write_json(output / "data_contract.json", contract)
    quality = {
        "source_rows": int(len(source)),
        "source_tsss_rows": int(source["Phân loại kho"].eq("TSSS").sum()),
        "output_rows": int(len(cleaned)),
        "output_columns": int(cleaned.shape[1]),
        "output_sha256": output_file_sha256(clean_path),
        "removed_invalid_target_or_date": removed_invalid,
        "outlier_rows_removed": 0,
        "target_min": float(cleaned["target_price_vnd_m2"].min()),
        "target_median": float(cleaned["target_price_vnd_m2"].median()),
        "target_p95": float(cleaned["target_price_vnd_m2"].quantile(0.95)),
        "target_p99": float(cleaned["target_price_vnd_m2"].quantile(0.99)),
        "target_max": float(cleaned["target_price_vnd_m2"].max()),
        "development_rows": split["development_rows"],
        "test_rows": split["test_rows"],
        "transaction_status_used_as_feature": False,
        "sensitive_raw_columns_in_output": [name for name in SENSITIVE_SOURCE_COLUMNS if name in cleaned.columns],
        "leakage_raw_columns_in_output": [name for name in LEAKAGE_SOURCE_COLUMNS if name in cleaned.columns]
    }
    write_json(output / "quality_report.json", quality)
    print(json.dumps(quality, ensure_ascii=False))
