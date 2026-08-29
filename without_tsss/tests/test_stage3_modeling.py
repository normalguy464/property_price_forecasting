from pathlib import Path
import json
import sys
import unittest

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from property_price_forecasting.modeling import file_sha256, regression_metrics


class StageThreeModelingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        artifact = PROJECT_ROOT / "artifacts" / "stage_03"
        cls.artifact = artifact
        cls.benchmark = json.loads((artifact / "benchmark_metrics.json").read_text(encoding="utf-8"))
        cls.best = json.loads((artifact / "best_params.json").read_text(encoding="utf-8"))
        cls.trials = json.loads((artifact / "optuna_trials.json").read_text(encoding="utf-8"))
        cls.rolling = json.loads((artifact / "rolling_metrics.json").read_text(encoding="utf-8"))
        cls.selected = json.loads((artifact / "selected_model.json").read_text(encoding="utf-8"))
        cls.oof = pd.read_json(artifact / "oof_predictions.jsonl.gz", orient="records", lines=True, compression="gzip")

    def test_metric_calculation(self):
        result = regression_metrics([100.0, 200.0], [110.0, 180.0])
        self.assertAlmostEqual(result["mae_vnd_m2"], 15.0)
        self.assertAlmostEqual(result["wape"], 0.1)
        self.assertAlmostEqual(result["within_10pct"], 1.0)

    def test_test_set_was_not_used(self):
        self.assertEqual(self.benchmark["test_rows_used"], 0)
        self.assertEqual(self.best["test_rows_used"], 0)
        self.assertEqual(self.rolling["test_rows_used"], 0)
        self.assertEqual(self.selected["test_rows_used"], 0)

    def test_benchmark_scope_is_limited(self):
        self.assertEqual(len(self.benchmark["models"]), 5)
        self.assertIn("hierarchical_median", self.benchmark["models"])
        self.assertIn("catboost_default", self.benchmark["models"])

    def test_optuna_budget_and_parameters(self):
        self.assertEqual(self.trials["total_trials"], 14)
        self.assertIn("depth", self.best["parameters"])
        self.assertIn("learning_rate", self.best["parameters"])
        self.assertGreater(self.best["recommended_full_iterations"], 0)

    def test_oof_scope(self):
        self.assertEqual(len(self.oof), 3334)
        self.assertEqual(self.oof["source_excel_row"].nunique(), 3334)
        self.assertLessEqual(pd.to_datetime(self.oof["as_of_date"]).max(), pd.Timestamp("2025-04-30"))
        self.assertTrue(np.isfinite(self.oof[["target", "prediction"]].to_numpy(dtype=float)).all())

    def test_selected_model_is_best_candidate(self):
        comparison = self.selected["candidate_comparison"]
        best_name = min(comparison, key=lambda name: comparison[name][self.selected["primary_metric"]])
        self.assertEqual(self.selected["model"], best_name)

    def test_model_artifact_integrity(self):
        model_path = PROJECT_ROOT / self.selected["model_path"]
        self.assertTrue(model_path.exists())
        self.assertEqual(self.selected["model_sha256"], file_sha256(model_path))


if __name__ == "__main__":
    unittest.main()
