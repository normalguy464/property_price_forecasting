from pathlib import Path
import json
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from property_price_forecasting_tsss.enhanced_market_features import build_enhanced_market_features, write_features, write_json


if __name__ == "__main__":
    config = json.loads((ROOT / "configs/pipeline.json").read_text(encoding="utf-8"))
    source = pd.read_excel((ROOT / config["source_file"]).resolve(), sheet_name=config["source_sheet"])
    base = pd.read_json((ROOT / config["base_cleaned_file"]).resolve(), lines=True, compression="gzip")
    current = pd.read_json(ROOT / "artifacts/market_features.jsonl.gz", lines=True, compression="gzip")
    if len(base) != len(current) or not base["source_excel_row"].equals(current["source_excel_row"]):
        raise RuntimeError("Current market feature alignment failed")
    features, manifest = build_enhanced_market_features(base, source, current, config)
    write_features(ROOT / "artifacts/enhanced_market_features.jsonl.gz", features)
    write_json(ROOT / "artifacts/enhanced_feature_manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False))
