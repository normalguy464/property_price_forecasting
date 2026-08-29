from pathlib import Path
import json
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from property_price_forecasting_wape.history_features import build_history_features, write_artifacts


if __name__ == "__main__":
    config = json.loads((ROOT / "configs/experiments.json").read_text(encoding="utf-8"))
    data = pd.read_json((ROOT / config["base_cleaned_file"]).resolve(), lines=True, compression="gzip")
    features, manifest = build_history_features(data, config)
    write_artifacts(features, manifest, ROOT / "artifacts")
    print(json.dumps(manifest, ensure_ascii=False))
