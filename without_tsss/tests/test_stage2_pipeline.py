from pathlib import Path
import json
import sys
import unittest

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from property_price_forecasting.cleaning import canonical_shape, normalize_text, output_file_sha256


class StageTwoPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        artifact = PROJECT_ROOT / "artifacts" / "stage_02"
        cls.clean_path = artifact / "cleaned_tstd.jsonl.gz"
        cls.cleaned = pd.read_json(cls.clean_path, orient="records", lines=True, compression="gzip")
        cls.contract = json.loads((artifact / "data_contract.json").read_text(encoding="utf-8"))
        cls.quality = json.loads((artifact / "quality_report.json").read_text(encoding="utf-8"))
        cls.splits = json.loads((artifact / "split_manifest.json").read_text(encoding="utf-8"))

    def test_business_contract(self):
        self.assertEqual(self.contract["target_unit"], "VND/m2")
        self.assertEqual(self.contract["population"], "TSTĐ only")
        self.assertFalse(self.contract["tsss_used"])
        self.assertEqual(self.contract["prediction_time"], "Thời điểm hiệu lực")
        self.assertEqual(set(self.contract["inference_provided_source_columns"]), {"Lợi thế kinh doanh", "Vị trí trong khung giá"})

    def test_row_counts_and_hash(self):
        self.assertEqual(len(self.cleaned), 7025)
        self.assertEqual(self.splits["development_rows"], 6025)
        self.assertEqual(self.splits["test_rows"], 1000)
        self.assertEqual(self.quality["output_sha256"], output_file_sha256(self.clean_path))

    def test_no_sensitive_or_leakage_raw_columns(self):
        self.assertEqual(self.quality["sensitive_raw_columns_in_output"], [])
        self.assertEqual(self.quality["leakage_raw_columns_in_output"], [])
        self.assertEqual(self.quality["tsss_rows_in_output"], 0)

    def test_feature_contract_is_complete(self):
        features = self.contract["categorical_features"] + self.contract["numeric_features"]
        self.assertTrue(set(features).issubset(self.cleaned.columns))
        self.assertEqual(self.cleaned[self.contract["categorical_features"]].isna().sum().sum(), 0)
        numeric = self.cleaned[self.contract["numeric_features"]].to_numpy(dtype=float)
        self.assertTrue(np.isfinite(numeric).all())
        self.assertTrue((self.cleaned["target_price_vnd_m2"] > 0).all())

    def test_split_is_strictly_temporal(self):
        dates = pd.to_datetime(self.cleaned["as_of_date"])
        development = self.cleaned["split"].eq("development")
        test = self.cleaned["split"].eq("test")
        self.assertLess(dates[development].max(), dates[test].min())
        self.assertEqual(self.splits["report_group_overlap_development_test"], 0)
        for fold in self.splits["folds"]:
            self.assertLess(pd.Timestamp(fold["train_end"]), pd.Timestamp(fold["validation_start"]))
            self.assertEqual(fold["report_group_overlap"], 0)

    def test_normalization(self):
        self.assertEqual(normalize_text("  Cân đối  "), "cân đối")
        self.assertEqual(canonical_shape("Không Cân đối "), "khong_can_doi")

    def test_target_diagnostics_are_not_features(self):
        features = set(self.contract["categorical_features"] + self.contract["numeric_features"])
        self.assertTrue(features.isdisjoint(self.contract["target_columns"]))
        self.assertTrue(features.isdisjoint(self.contract["diagnostic_columns"]))


if __name__ == "__main__":
    unittest.main()
