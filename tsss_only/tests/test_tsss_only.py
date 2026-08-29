from pathlib import Path
import json
import unittest

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


class TsssOnlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stage2 = ROOT / "artifacts/stage_02"
        cls.stage3 = ROOT / "artifacts/stage_03"
        cls.contract = json.loads((cls.stage2 / "data_contract.json").read_text(encoding="utf-8"))
        cls.quality = json.loads((cls.stage2 / "quality_report.json").read_text(encoding="utf-8"))
        cls.benchmark = json.loads((cls.stage3 / "benchmark_results.json").read_text(encoding="utf-8"))
        cls.final = json.loads((cls.stage3 / "final_results.json").read_text(encoding="utf-8"))
        cls.external = json.loads((cls.stage3 / "external_tstd_test_results.json").read_text(encoding="utf-8"))
        cls.data = pd.read_json(cls.stage2 / "cleaned_tsss.jsonl.gz", lines=True, compression="gzip")

    def test_tsss_population_and_target(self):
        self.assertEqual(len(self.data), 27452)
        self.assertEqual(self.contract["population"], "TSSS only")
        self.assertEqual(self.contract["target_source_column"], "Đơn giá quyền sử dụng đất (đ/m2)1")
        self.assertEqual(self.quality["removed_invalid_target_or_date"], 0)

    def test_transaction_status_is_excluded(self):
        self.assertFalse(self.contract["transaction_status_used_as_feature"])
        self.assertIn("Tình trạng giao dịch", self.contract["excluded_source_columns"])
        self.assertNotIn("Tình trạng giao dịch", self.data.columns)

    def test_imbalance_variants_are_rolling_only(self):
        names = {value["variant"] for value in self.benchmark["candidates"]}
        self.assertTrue({"catboost_log", "catboost_raw", "catboost_weighted", "catboost_oversampled"}.issubset(names))
        self.assertFalse(self.benchmark["test_used_for_selection"])
        self.assertEqual(self.benchmark["selected_variant"], "catboost_log")

    def test_final_temporal_holdout(self):
        self.assertTrue(self.final["test_is_temporal_holdout_not_used_for_selection"])
        self.assertFalse(self.final["transaction_status_used_as_feature"])
        self.assertEqual(self.final["test_rows"], 3706)

    def test_external_tstd_test_never_uses_tstd_for_training(self):
        self.assertEqual(self.external["population"], "TSTĐ only")
        self.assertEqual(self.external["rows"], 1000)
        self.assertEqual(self.external["tstd_rows_used_for_training_or_selection"], 0)
        self.assertGreater(self.external["metrics"]["mape"], 0.50)


if __name__ == "__main__":
    unittest.main()
