from pathlib import Path
import json
import sys
import argparse

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from property_price_forecasting_wape.retrieval_report import build_retrieval_quality_report, write_retrieval_report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-k", type=int)
    arguments = parser.parse_args()
    config = json.loads((ROOT / "configs/experiments.json").read_text(encoding="utf-8"))
    if arguments.top_k is not None:
        if arguments.top_k <= 0:
            raise ValueError("top_k must be positive")
        config["retrieval_quality_report"]["top_k"] = arguments.top_k
    base = pd.read_json((ROOT / config["base_cleaned_file"]).resolve(), lines=True, compression="gzip")
    source_path = (ROOT / config["comparable_retrieval"]["source_file"]).resolve()
    source = pd.read_excel(source_path, sheet_name=config["comparable_retrieval"]["source_sheet"])
    progress = lambda completed, total: print(f"retrieval_rows={completed}/{total}", flush=True)
    detail, report = build_retrieval_quality_report(base, source, config, progress)
    suffix = "" if arguments.top_k is None else f"_k{arguments.top_k}"
    write_retrieval_report(detail, report, ROOT / "artifacts", suffix)
    print(json.dumps(report, ensure_ascii=False))
