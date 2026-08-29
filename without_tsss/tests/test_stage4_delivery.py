from hashlib import sha256
from pathlib import Path
import gzip
import json
import sys
import unittest

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from property_price_forecasting.inference import predict_records
from property_price_forecasting.modeling import regression_metrics


class StageFourDeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output = ROOT / "artifacts/stage_04"
        cls.config = json.loads((ROOT / "configs/stage4.json").read_text(encoding="utf-8"))
        cls.manifest = json.loads((cls.output / "evaluation_manifest.json").read_text(encoding="utf-8"))
        cls.metrics = json.loads((cls.output / "test_metrics.json").read_text(encoding="utf-8"))
        cls.predictions = pd.read_json(cls.output / "test_predictions.jsonl.gz", lines=True, compression="gzip")

    def test_locked_test_scope(self):
        self.assertEqual(self.manifest["evaluation_run_count"], 1)
        self.assertEqual(self.manifest["test_rows"], 1000)
        self.assertEqual(self.manifest["test_date_min"], "2025-05-04")
        self.assertEqual(self.manifest["test_date_max"], "2025-07-31")
        self.assertFalse(self.manifest["test_was_used_for_fit_tuning_or_calibration"])
        self.assertTrue(self.manifest["test_was_used_for_final_evaluation_only"])

    def test_prediction_artifact_integrity(self):
        self.assertEqual(len(self.predictions), 1000)
        self.assertEqual(self.predictions["evaluation_row_id"].nunique(), 1000)
        digest = sha256((self.output / "test_predictions.jsonl.gz").read_bytes()).hexdigest()
        self.assertEqual(digest, self.manifest["test_predictions_sha256"])

    def test_metrics_are_reproducible_from_frozen_predictions(self):
        computed = regression_metrics(self.predictions["target"], self.predictions["prediction"])
        for name, value in computed.items():
            self.assertAlmostEqual(value, self.metrics["overall"][name], places=7)

    def test_intervals_and_coverage(self):
        for level in [80, 90, 95]:
            lower = self.predictions[f"lower_{level}"]
            upper = self.predictions[f"upper_{level}"]
            self.assertTrue((lower <= self.predictions["prediction"]).all())
            self.assertTrue((upper >= self.predictions["prediction"]).all())
            observed = ((self.predictions["target"] >= lower) & (self.predictions["target"] <= upper)).mean()
            self.assertAlmostEqual(observed, self.metrics["interval_coverage"][str(level / 100)]["observed"], places=7)

    def test_acceptance_is_consistent(self):
        checks = self.metrics["acceptance_checks"]
        self.assertEqual(self.metrics["accepted"], all(checks.values()))
        self.assertTrue(set(self.predictions["status"]).issubset({"automatic", "manual_review", "reject"}))

    def test_rare_ward_requires_manual_review(self):
        rare = self.predictions["ward_frequency"].eq("rare")
        self.assertGreater(int(rare.sum()), 0)
        self.assertTrue(self.predictions.loc[rare, "status"].eq("manual_review").all())
        self.assertTrue(self.predictions.loc[rare, "flags"].str.contains("rare_ward").all())

    def test_model_checksum_unchanged(self):
        model = ROOT / self.config["model_path"]
        digest = sha256(model.read_bytes()).hexdigest()
        self.assertEqual(digest, self.manifest["model_sha256"])

    def test_inference_smoke_and_contract(self):
        package = self.output / "model_package"
        example = json.loads((package / "example_input.json").read_text(encoding="utf-8"))
        expected = json.loads((package / "example_output.json").read_text(encoding="utf-8"))
        actual = predict_records(example, ROOT / self.config["model_path"], self.output / "domain_profile.json", self.output / "calibration.json", self.config)
        self.assertAlmostEqual(actual[0]["prediction_vnd_m2"], expected[0]["prediction_vnd_m2"], places=6)
        self.assertGreater(actual[0]["prediction_vnd_m2"], 0)
        contract = json.loads((package / "inference_contract.json").read_text(encoding="utf-8"))
        self.assertFalse(contract["tsss_allowed"])
        self.assertNotIn("target_price_vnd_m2", contract["required_inputs"])

    def test_stale_model_date_is_rejected(self):
        package = self.output / "model_package"
        example = json.loads((package / "example_input.json").read_text(encoding="utf-8"))
        example[0]["as_of_date"] = "2025-08-01"
        actual = predict_records(example, ROOT / self.config["model_path"], self.output / "domain_profile.json", self.output / "calibration.json", self.config)
        self.assertEqual(actual[0]["status"], "reject")
        self.assertIn("unsupported_as_of_date", actual[0]["flags"])


if __name__ == "__main__":
    unittest.main()
