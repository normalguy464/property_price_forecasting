from hashlib import sha256
from pathlib import Path
import ast
import json
import sys
import unittest

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from property_price_forecasting_tsss.inference import predict_records
from property_price_forecasting_tsss.comparable_retrieval import retrieve_comparables
from property_price_forecasting_tsss.market_features import build_market_features
from property_price_forecasting_tsss.modeling import price_band_sample_weights, regression_metrics


class WithTsssPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((ROOT / "configs/pipeline.json").read_text(encoding="utf-8"))
        cls.audit = json.loads((ROOT / "artifacts/tsss_audit.json").read_text(encoding="utf-8"))
        cls.features = pd.read_json(ROOT / "artifacts/market_features.jsonl.gz", lines=True, compression="gzip")
        cls.feature_manifest = json.loads((ROOT / "artifacts/feature_manifest.json").read_text(encoding="utf-8"))
        cls.final = json.loads((ROOT / "artifacts/final_results.json").read_text(encoding="utf-8"))
        cls.model_manifest = json.loads((ROOT / "artifacts/model_manifest.json").read_text(encoding="utf-8"))
        cls.oof = pd.read_json(ROOT / "artifacts/oof_predictions.jsonl.gz", lines=True, compression="gzip")
        cls.test = pd.read_json(ROOT / "artifacts/reused_test_predictions.jsonl.gz", lines=True, compression="gzip")
        cls.enhanced_features = pd.read_json(ROOT / "artifacts/enhanced_market_features.jsonl.gz", lines=True, compression="gzip")
        cls.enhanced_manifest = json.loads((ROOT / "artifacts/enhanced_feature_manifest.json").read_text(encoding="utf-8"))
        cls.enhanced_benchmark = json.loads((ROOT / "artifacts/enhanced_mape_benchmark.json").read_text(encoding="utf-8"))
        cls.learned_comparable = json.loads((ROOT / "artifacts/learned_comparable_experiment.json").read_text(encoding="utf-8"))
        cls.learned_comparable_oof = pd.read_json(ROOT / "artifacts/learned_comparable_oof_predictions.jsonl.gz", lines=True, compression="gzip")

    def test_tsss_audit_population(self):
        self.assertEqual(self.audit["tsss_rows"], 27452)
        self.assertEqual(self.audit["eligible_tsss_rows"], 27425)
        self.assertEqual(self.audit["date_quality"]["market_after_effective"], 26)
        self.assertEqual(self.audit["date_quality"]["market_older_than_maximum"], 1)

    def test_feature_contract_and_alignment(self):
        self.assertEqual(len(self.features), 7025)
        self.assertEqual(self.features["source_excel_row"].nunique(), 7025)
        self.assertEqual(len(self.feature_manifest["market_features"]), 86)
        self.assertEqual(set(self.features.columns), {"source_excel_row", *self.feature_manifest["market_features"]})
        values = self.features.drop(columns=["source_excel_row"]).to_numpy(dtype=float)
        self.assertEqual(int(np.isinf(values).sum()), 0)
        sensitive = {"Mã kho", "Mã tài sản", "Số báo cáo định giá", "Chi tiết", "Thông tin liên hệ"}
        self.assertFalse(set(self.features.columns) & sensitive)

    def test_leakage_guards_are_declared(self):
        guards = set(self.feature_manifest["leakage_guards"])
        self.assertIn("availability_date_strictly_before_target", guards)
        self.assertIn("market_date_strictly_before_target", guards)
        self.assertIn("same_report_excluded", guards)
        forbidden = ["Don_gia_TB", "Min", "Max", "Độ lệch chuẩn", "Số lượng mẫu"]
        self.assertFalse(any(name in self.feature_manifest["market_features"] for name in forbidden))

    def test_asof_and_same_report_are_enforced(self):
        base = pd.DataFrame([{
            "source_excel_row": -1, "as_of_date": "2025-01-10", "district": "d", "ward_new": "w", "road": "r", "price_position": "vt1", "land_use": "dat_o_do_thi",
            "plot_shape": "can_doi", "business_advantage": "trung_binh", "area_m2": 100.0, "frontage_m": 5.0, "length_m": 20.0, "distance_to_main_road_m": 0.0, "alley_width_m": 5.0,
        }])
        common = {
            "Phân loại kho": "TSSS", "Diện tích (m2)": 100.0, "Giá giao dịch/rao bán (đ)": 10000000000, "Giá ước tính (đ)": 9500000000, "Thành phố/Quận/Huyện/Thị xã": "d",
            "Xã/Phường mới": "w", "Đường phố": "r", "Vị trí trong khung giá": "vt1", "Mục đích sử dụng đất": "Đất ở đô thị", "Hình dáng": "Cân đối", "Lợi thế kinh doanh": "Trung bình",
            "Kích thước mặt tiền (m)": 5.0, "Kích thước chiều dài": 20.0, "Khoảng cách đến đường chính (m)": 0.0, "Độ rộng ngõ/ngách nhỏ nhất (Từ đường chính đến BĐS)": 5.0,
            "Tình trạng giao dịch": "Chưa giao dịch",
        }
        rows = []
        for report, market_date, availability_date in [("ok", "08/01/2025", "09/01/2025"), ("same_day_availability", "08/01/2025", "10/01/2025"), ("same_day_market", "10/01/2025", "09/01/2025"), ("target_report", "08/01/2025", "09/01/2025")]:
            rows.append({**common, "Số báo cáo định giá": report, "Thời điểm giao dịch/rao bán (đ)": market_date, "Thời điểm hiệu lực": availability_date})
        features, _ = build_market_features(base, pd.DataFrame(rows), self.config, ["target_report"])
        self.assertEqual(features.loc[0, "market_road_count_90d"], 1.0)

    def test_tsss_is_not_target(self):
        self.assertEqual(self.model_manifest["tsss_used_as_target_rows"], 0)
        self.assertTrue(self.model_manifest["tsss_used_as_historical_feature_source"])
        self.assertEqual(self.model_manifest["development_rows"], 6025)

    def test_rolling_selection_and_improvement(self):
        benchmark = json.loads((ROOT / "artifacts/benchmark_results.json").read_text(encoding="utf-8"))
        old = next(value for value in benchmark["candidates"] if value["variant"] == "ridge_without_tsss_frozen")
        self.assertFalse(self.final["test_used_for_selection"])
        self.assertLess(self.final["rolling_metrics"]["mae_vnd_m2"], old["pooled"]["mae_vnd_m2"])
        self.assertEqual(self.final["selected"], "catboost_with_tsss_tuned")
        trials = json.loads((ROOT / "artifacts/tuning_trials.json").read_text(encoding="utf-8"))
        self.assertEqual(len(trials), 6)
        self.assertTrue(all(value["state"] == "COMPLETE" for value in trials))

    def test_oof_scope_and_metrics(self):
        self.assertEqual(len(self.oof), 3334)
        self.assertEqual(self.oof["row_index"].nunique(), 3334)
        self.assertLessEqual(self.oof["as_of_date"].max(), "2025-04-30")
        computed = regression_metrics(self.oof["target"], self.oof["prediction"])
        for name, value in computed.items():
            self.assertAlmostEqual(value, self.final["rolling_metrics"][name], places=7)

    def test_reused_test_is_non_confirmatory(self):
        self.assertEqual(len(self.test), 1000)
        self.assertTrue(self.model_manifest["test_is_reused_non_confirmatory"])
        computed = regression_metrics(self.test["target"], self.test["prediction"])
        for name, value in computed.items():
            self.assertAlmostEqual(value, self.final["reused_test_non_confirmatory"]["with_tsss"][name], places=7)

    def test_model_checksum(self):
        path = ROOT / self.model_manifest["model_path"]
        self.assertEqual(sha256(path.read_bytes()).hexdigest(), self.model_manifest["model_sha256"])

    def test_price_band_weights_are_fitted_from_train_target_only(self):
        weights, manifest = price_band_sample_weights([40_000_000, 41_000_000, 42_000_000, 250_000_000], 2.0)
        self.assertEqual(len(weights), 4)
        self.assertAlmostEqual(float(weights.mean()), 1.0, places=12)
        self.assertGreater(weights[-1], weights[0])
        self.assertEqual(manifest["bands"]["below_60m"], 3)
        self.assertEqual(manifest["bands"]["at_least_200m"], 1)

    def test_enhanced_feature_artifact(self):
        self.assertEqual(len(self.enhanced_features), 7025)
        self.assertEqual(self.enhanced_manifest["enhanced_feature_count"], 33)
        self.assertEqual(self.enhanced_manifest["comparable_v2_feature_count"], 15)
        self.assertEqual(self.enhanced_manifest["temporal_market_feature_count"], 18)
        self.assertEqual(self.enhanced_features["source_excel_row"].nunique(), 7025)
        values = self.enhanced_features.drop(columns=["source_excel_row"]).to_numpy(dtype=float)
        self.assertEqual(int(np.isinf(values).sum()), 0)
        self.assertIn("availability_date_strictly_before_target", self.enhanced_manifest["leakage_guards"])

    def test_enhanced_benchmark_does_not_promote_worse_model(self):
        self.assertFalse(self.enhanced_benchmark["test_used_for_selection"])
        self.assertFalse(self.enhanced_benchmark["model_promoted"])
        self.assertEqual(len(self.enhanced_benchmark["candidates"]), 5)
        self.assertEqual(self.enhanced_benchmark["status"], "no_improvement_keep_current_model")
        self.assertGreaterEqual(self.enhanced_benchmark["selected_pooled"]["mape"], self.enhanced_benchmark["baseline"]["pooled"]["mape"])

    def test_learned_comparable_experiment_is_asof_and_reproducible(self):
        manifest = self.learned_comparable["pair_manifest"]
        self.assertFalse(self.learned_comparable["test_used_for_selection"])
        self.assertFalse(self.learned_comparable["base_model_changed"])
        self.assertEqual(manifest["target_rows"], 7025)
        self.assertEqual(manifest["candidate_pool_size"], 30)
        self.assertIn("availability_date_strictly_before_target", manifest["leakage_guards"])
        self.assertIn("target_labels_fit_on_train_rows_only", manifest["leakage_guards"])
        selected = self.learned_comparable["rolling_oof"]["selected_blend"]
        computed = regression_metrics(self.learned_comparable_oof["target"], self.learned_comparable_oof[selected])
        expected = self.learned_comparable["rolling_oof"]["blends"][selected]
        for name, value in computed.items():
            self.assertAlmostEqual(value, expected[name], places=7)
        self.assertLess(expected["mae_vnd_m2"], self.learned_comparable["rolling_oof"]["frozen_with_tsss"]["mae_vnd_m2"])
        forbidden = {"Mã kho", "Mã tài sản", "Số báo cáo định giá", "Chi tiết", "Thông tin liên hệ"}
        self.assertFalse(set(self.learned_comparable_oof.columns) & forbidden)

    def test_inference_smoke_and_stale_guard(self):
        package = ROOT / "artifacts/model_package"
        example = json.loads((package / "example_input.json").read_text(encoding="utf-8"))
        expected = json.loads((package / "example_output.json").read_text(encoding="utf-8"))
        calibration = json.loads((package / "calibration.json").read_text(encoding="utf-8"))
        source = pd.read_excel((ROOT / self.config["source_file"]).resolve(), sheet_name=self.config["source_sheet"])
        actual = predict_records(example, source, ROOT / self.model_manifest["model_path"], self.model_manifest, self.config, calibration)
        self.assertAlmostEqual(actual[0]["prediction_vnd_m2"], expected[0]["prediction_vnd_m2"], places=6)
        self.assertIn("0.9", actual[0]["prediction_intervals"])
        example[0]["as_of_date"] = "2025-08-01"
        stale = predict_records(example, source, ROOT / self.model_manifest["model_path"], self.model_manifest, self.config, calibration)
        self.assertEqual(stale[0]["status"], "reject")
        self.assertIn("unsupported_as_of_date", stale[0]["flags"])

    def test_comparable_retrieval_is_asof_private_and_ranked(self):
        target = dict(self.config["example_input"])
        target["report_reference"] = "same_report"
        source_rows = []
        for number, report, market_date, availability_date, area, price in [
            (1, "eligible_1", "10/07/2025", "11/07/2025", 80.0, 8_000_000_000),
            (2, "eligible_2", "01/07/2025", "02/07/2025", 82.0, 8_200_000_000),
            (3, "eligible_3", "20/06/2025", "21/06/2025", 78.0, 7_800_000_000),
            (4, "same_report", "10/07/2025", "11/07/2025", 80.0, 8_000_000_000),
            (5, "future_market", "15/07/2025", "14/07/2025", 80.0, 8_000_000_000),
            (6, "future_availability", "10/07/2025", "15/07/2025", 80.0, 8_000_000_000),
        ]:
            source_rows.append({
                "Phân loại kho": "TSSS", "Số báo cáo định giá": report, "Thời điểm giao dịch/rao bán (đ)": market_date, "Thời điểm hiệu lực": availability_date,
                "Diện tích (m2)": area, "Giá giao dịch/rao bán (đ)": price, "Giá ước tính (đ)": price * 0.95,
                "Thành phố/Quận/Huyện/Thị xã": "Thành phố Thủ Đức", "Xã/Phường mới": "Phường Long Trường", "Đường phố": "Nguyễn Duy Trinh - Quận 9 cũ",
                "Vị trí trong khung giá": "VT2", "Mục đích sử dụng đất": "Đất ở đô thị", "Hình dáng": "Cân đối", "Lợi thế kinh doanh": "Trung bình",
                "Kích thước mặt tiền (m)": 4.7, "Kích thước chiều dài": 17.06, "Khoảng cách đến đường chính (m)": 100.0,
                "Độ rộng ngõ/ngách nhỏ nhất (Từ đường chính đến BĐS)": 7.0, "Tình trạng giao dịch": "Đã giao dịch",
                "Mã kho": f"private-{number}", "Mã tài sản": f"asset-{number}", "Chi tiết": "private address", "Thông tin liên hệ": "private contact",
            })
        output = retrieve_comparables([target], pd.DataFrame(source_rows), self.config, 3)[0]
        self.assertEqual(output["status"], "automatic")
        self.assertEqual(output["returned_comparable_count"], 3)
        self.assertEqual([value["comparable_reference"] for value in output["comparables"]], ["TSSS-000002", "TSSS-000003", "TSSS-000004"])
        self.assertTrue(all(value["market_date"] < target["as_of_date"] for value in output["comparables"]))
        self.assertTrue(all(value["age_days"] > 0 for value in output["comparables"]))
        rendered = json.dumps(output, ensure_ascii=False)
        self.assertNotIn("private-", rendered)
        self.assertNotIn("asset-", rendered)
        self.assertNotIn("private address", rendered)
        self.assertNotIn("private contact", rendered)

    def test_comparable_retrieval_rejects_invalid_request(self):
        target = dict(self.config["example_input"])
        target["as_of_date"] = "2025-08-01"
        output = retrieve_comparables([target], pd.DataFrame(), self.config, 3)[0]
        self.assertEqual(output["status"], "reject")
        self.assertEqual(output["flags"], ["unsupported_as_of_date"])
        with self.assertRaises(ValueError):
            retrieve_comparables([self.config["example_input"]], pd.DataFrame(), self.config, 2)

    def test_python_code_has_no_comments(self):
        for path in list((ROOT / "src").rglob("*.py")) + list((ROOT / "scripts").rglob("*.py")) + list((ROOT / "tests").rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            self.assertIsNotNone(tree)
            for line in path.read_text(encoding="utf-8").splitlines():
                self.assertFalse(line.lstrip().startswith("#"), str(path))


if __name__ == "__main__":
    unittest.main()
