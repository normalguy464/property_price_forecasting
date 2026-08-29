from pathlib import Path
import json
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from property_price_forecasting_tsss.audit import audit_tsss, write_json


if __name__ == "__main__":
    config = json.loads((ROOT / "configs/pipeline.json").read_text(encoding="utf-8"))
    source = pd.read_excel((ROOT / config["source_file"]).resolve(), sheet_name=config["source_sheet"])
    result = audit_tsss(source, config)
    write_json(ROOT / "artifacts/tsss_audit.json", result)
    print(json.dumps(result, ensure_ascii=False))
