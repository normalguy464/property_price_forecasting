from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from property_price_forecasting.audit import write_audit


source = PROJECT_ROOT.parent.parent / "Train_noi.xlsx"
output = PROJECT_ROOT / "artifacts" / "stage_01" / "data_profile.json"
result = write_audit(source, output)
print(f"rows={result['source']['rows']}")
print(f"columns={result['source']['columns']}")
print(f"output={output}")
