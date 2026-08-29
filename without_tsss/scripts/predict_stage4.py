from pathlib import Path
import argparse
import json
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from property_price_forecasting.inference import predict_records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("output_json")
    arguments = parser.parse_args()
    config = json.loads((ROOT / "configs/stage4.json").read_text(encoding="utf-8"))
    records = json.loads(Path(arguments.input_json).read_text(encoding="utf-8"))
    result = predict_records(records, ROOT / config["model_path"], ROOT / "artifacts/stage_04/domain_profile.json", ROOT / "artifacts/stage_04/calibration.json", config)
    Path(arguments.output_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
