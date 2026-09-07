from pathlib import Path
import argparse
import json
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from property_price_forecasting_wape.comparable_retrieval import retrieve_comparables


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("output_json")
    parser.add_argument("--market-xlsx")
    parser.add_argument("--count", type=int, default=3)
    arguments = parser.parse_args()
    config = json.loads((ROOT / "configs/experiments.json").read_text(encoding="utf-8"))
    source_path = Path(arguments.market_xlsx) if arguments.market_xlsx else (ROOT / config["comparable_retrieval"]["source_file"]).resolve()
    records = json.loads(Path(arguments.input_json).read_text(encoding="utf-8"))
    source = pd.read_excel(source_path, sheet_name=config["comparable_retrieval"]["source_sheet"])
    output = retrieve_comparables(records, source, config, arguments.count)
    Path(arguments.output_json).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
