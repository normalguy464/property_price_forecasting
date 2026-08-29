from pathlib import Path
import json
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from property_price_forecasting_tsss.market_features import build_market_features, write_features, write_json


if __name__ == "__main__":
    config = json.loads((ROOT / "configs/pipeline.json").read_text(encoding="utf-8"))
    source = pd.read_excel((ROOT / config["source_file"]).resolve(), sheet_name=config["source_sheet"])
    base = pd.read_json((ROOT / config["base_cleaned_file"]).resolve(), lines=True, compression="gzip")
    features, manifest = build_market_features(base, source, config)
    write_features(ROOT / "artifacts/market_features.jsonl.gz", features)
    write_json(ROOT / "artifacts/feature_manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False))
