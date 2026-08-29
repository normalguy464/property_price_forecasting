from pathlib import Path
import argparse
import json
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from property_price_forecasting_tsss.inference import predict_records


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("market_xlsx")
    parser.add_argument("output_json")
    arguments = parser.parse_args()
    config = json.loads((ROOT / "configs/pipeline.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "artifacts/model_manifest.json").read_text(encoding="utf-8"))
    records = json.loads(Path(arguments.input_json).read_text(encoding="utf-8"))
    source = pd.read_excel(arguments.market_xlsx, sheet_name=config["source_sheet"])
    calibration = json.loads((ROOT / "artifacts/model_package/calibration.json").read_text(encoding="utf-8"))
    output = predict_records(records, source, ROOT / manifest["model_path"], manifest, config, calibration)
    Path(arguments.output_json).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
