from pathlib import Path
import json
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from property_price_forecasting.cleaning import CATEGORICAL_FEATURES, DIAGNOSTIC_COLUMNS, LEAKAGE_SOURCE_COLUMNS, METADATA_COLUMNS, NUMERIC_FEATURES, SENSITIVE_SOURCE_COLUMNS, TARGET_COLUMNS, clean_tstd, output_file_sha256, source_file_sha256, write_clean_jsonl, write_json
from property_price_forecasting.splitting import build_split_manifest


config_path = PROJECT_ROOT / "configs" / "stage2.json"
config = json.loads(config_path.read_text(encoding="utf-8"))
source_path = (PROJECT_ROOT / config["source_file"]).resolve()
output_dir = PROJECT_ROOT / "artifacts" / "stage_02"
clean_path = output_dir / "cleaned_tstd.jsonl.gz"
contract_path = output_dir / "data_contract.json"
quality_path = output_dir / "quality_report.json"
split_path = output_dir / "split_manifest.json"
source = pd.read_excel(source_path, sheet_name=config["source_sheet"])
cleaned, removed_invalid = clean_tstd(source, config)
write_clean_jsonl(clean_path, cleaned)
split_manifest = build_split_manifest(cleaned, config)
write_json(split_path, split_manifest)
contract = {
    "version": "stage2-v1",
    "source_file": source_path.name,
    "source_sha256": source_file_sha256(source_path),
    "population": "TSTĐ only",
    "tsss_used": False,
    "prediction_object": config["prediction_object"],
    "prediction_time": "Thời điểm hiệu lực",
    "target": "target_price_vnd_m2",
    "target_unit": config["target_unit"],
    "categorical_features": CATEGORICAL_FEATURES,
    "numeric_features": NUMERIC_FEATURES,
    "metadata_columns": METADATA_COLUMNS,
    "target_columns": TARGET_COLUMNS,
    "diagnostic_columns": DIAGNOSTIC_COLUMNS,
    "leakage_source_columns": LEAKAGE_SOURCE_COLUMNS,
    "sensitive_source_columns": SENSITIVE_SOURCE_COLUMNS,
    "macro_features_used": [],
    "historical_target_aggregates_used": [],
    "inference_provided_source_columns": config["inference_provided_columns"],
    "outlier_rows_removed": 0,
    "invalid_target_or_date_rows_removed": removed_invalid,
}
write_json(contract_path, contract)
quality = {
    "source_rows": int(len(source)),
    "source_tstd_rows": int(source["Phân loại kho"].eq(config["eligible_warehouse_class"]).sum()),
    "output_rows": int(len(cleaned)),
    "output_columns": int(cleaned.shape[1]),
    "output_sha256": output_file_sha256(clean_path),
    "removed_invalid_target_or_date": removed_invalid,
    "outlier_rows_removed": 0,
    "categorical_missing_tokens": {name: int(cleaned[name].eq("__missing__").sum()) for name in CATEGORICAL_FEATURES},
    "categorical_cardinality": {name: int(cleaned[name].nunique()) for name in CATEGORICAL_FEATURES},
    "numeric_missing": {name: int(cleaned[name].isna().sum()) for name in NUMERIC_FEATURES},
    "target_min": float(cleaned["target_price_vnd_m2"].min()),
    "target_median": float(cleaned["target_price_vnd_m2"].median()),
    "target_p95": float(cleaned["target_price_vnd_m2"].quantile(0.95)),
    "target_p99": float(cleaned["target_price_vnd_m2"].quantile(0.99)),
    "target_max": float(cleaned["target_price_vnd_m2"].max()),
    "quality_flag_counts": {name: int(cleaned[name].sum()) for name in NUMERIC_FEATURES + DIAGNOSTIC_COLUMNS if name.startswith("quality_")},
    "development_rows": split_manifest["development_rows"],
    "test_rows": split_manifest["test_rows"],
    "test_rows_with_asset_seen_in_development": split_manifest["test_rows_with_asset_seen_in_development"],
    "test_rows_with_new_asset": split_manifest["test_rows_with_new_asset"],
    "tsss_rows_in_output": 0,
    "sensitive_raw_columns_in_output": [name for name in SENSITIVE_SOURCE_COLUMNS if name in cleaned.columns],
    "leakage_raw_columns_in_output": [name for name in LEAKAGE_SOURCE_COLUMNS if name in cleaned.columns],
}
write_json(quality_path, quality)
print(f"source_rows={len(source)}")
print(f"tstd_rows={len(cleaned)}")
print(f"development_rows={split_manifest['development_rows']}")
print(f"test_rows={split_manifest['test_rows']}")
print(f"output={clean_path}")
