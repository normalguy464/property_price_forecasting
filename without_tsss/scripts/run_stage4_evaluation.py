from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from property_price_forecasting.evaluation import evaluate_stage4


if __name__ == "__main__":
    result = evaluate_stage4(ROOT, "configs/stage4.json")
    print(result)
