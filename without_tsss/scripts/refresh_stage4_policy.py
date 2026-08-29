from pathlib import Path
import json
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from property_price_forecasting.modeling import file_sha256, segmented_metrics


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    output = ROOT / "artifacts/stage_04"
    predictions_path = output / "test_predictions.jsonl.gz"
    predictions = pd.read_json(predictions_path, lines=True, compression="gzip")
    rare = predictions["ward_frequency"].eq("rare")
    for index in predictions.index[rare]:
        flags = [value for value in str(predictions.at[index, "flags"]).split("|") if value]
        flags.append("rare_ward")
        predictions.at[index, "flags"] = "|".join(sorted(set(flags)))
        if predictions.at[index, "status"] != "reject":
            predictions.at[index, "status"] = "manual_review"
    compression = {"method": "gzip", "compresslevel": 6, "mtime": 0}
    predictions.to_json(predictions_path, orient="records", lines=True, compression=compression, force_ascii=False, double_precision=15)
    segment_columns = ["month", "district", "ward_new", "road_frequency", "ward_frequency", "price_band", "warehouse_type", "data_quality", "business_advantage", "price_position", "asset_history", "status"]
    write_json(output / "segment_metrics.json", segmented_metrics(predictions, segment_columns))
    baseline_path = output / "model_package/monitoring_baseline.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    baseline["test_status_rates"] = {str(key): float(value) for key, value in predictions["status"].value_counts(normalize=True).items()}
    write_json(baseline_path, baseline)
    manifest_path = output / "evaluation_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["test_predictions_sha256"] = file_sha256(predictions_path)
    manifest["post_evaluation_policy_refresh"] = "rare_ward_manual_review_without_reprediction"
    write_json(manifest_path, manifest)
