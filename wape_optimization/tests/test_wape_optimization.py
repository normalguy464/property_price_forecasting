from hashlib import sha256
from pathlib import Path
import io
import json
import sys
import tokenize
import unittest

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from property_price_forecasting_wape.experiments import metrics
from property_price_forecasting_wape.comparable_retrieval import retrieve_comparables
from property_price_forecasting_wape.history_features import build_history_features
from property_price_forecasting_wape.retrieval_report import build_retrieval_quality_report, price_metrics


def load_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_history_artifact_contract():
    manifest = load_json("artifacts/history_manifest.json")
    frame = pd.read_json(ROOT / "artifacts/history_features.jsonl.gz", lines=True, compression="gzip")
    assert frame.shape == (7025, 59)
    assert manifest["feature_count"] == 58
    assert frame["source_excel_row"].is_unique
    assert not np.isinf(frame.select_dtypes(include="number").to_numpy()).any()


def test_history_uses_only_available_prior_labels():
    frame = pd.DataFrame({
        "source_excel_row": [1, 2, 3, 4],
        "as_of_date": ["2025-01-01", "2025-01-05", "2025-01-01", "2025-01-10"],
        "target_price_vnd_m2": [100.0, 500.0, 300.0, 900.0],
        "district": ["D", "D", "D", "D"],
        "ward_new": ["W", "W", "W", "W"],
        "road": ["R", "R", "R", "R"],
        "report_group_id": ["A", "B", "C", "C"],
        "asset_group_id": ["X", "X", "X", "X"],
    })
    config = {
        "label_availability_lag_days": 7,
        "history_windows_days": [90, 180, 365],
        "history_road_min_count": 1,
        "history_ward_min_count": 1,
        "history_district_min_count": 1,
    }
    result, _ = build_history_features(frame, config)
    current = result.iloc[3]
    assert current["history_road_count_365d"] == 1
    assert current["history_road_median_365d"] == 100.0
    assert current["history_asset_count"] == 1
    assert current["history_asset_last_price"] == 100.0


def test_experiment_is_separate_from_frozen_branches():
    config = load_json("configs/experiments.json")
    external = [value for key, value in config.items() if key.endswith("_file")]
    assert all(value.startswith("../without_tsss/") or value.startswith("../with_tsss/") for value in external)
    assert all((ROOT / value).resolve().exists() for value in external)


def test_selected_oof_metrics_reproduce():
    expected = load_json("artifacts/final_results.json")["rolling_metrics"]
    frame = pd.read_json(ROOT / "artifacts/selected_oof_predictions.jsonl.gz", lines=True, compression="gzip")
    actual = metrics(frame["target"], frame["prediction"])
    assert len(frame) == 3334
    assert frame["row_index"].is_unique
    for key in expected:
        assert np.isclose(actual[key], expected[key], rtol=0, atol=1e-9)


def test_selected_solution_improves_both_frozen_pipelines():
    result = load_json("artifacts/final_results.json")
    selected = result["rolling_metrics"]
    comparison = result["rolling_comparison"]
    assert selected["wape"] < comparison["with_tsss"]["wape"]
    assert selected["wape"] < comparison["without_tsss"]["wape"]
    assert selected["mae_vnd_m2"] < comparison["with_tsss"]["mae_vnd_m2"]
    assert not result["target_reached"]
    assert selected["wape"] > result["target_wape"]


def test_solution_manifest_and_component_hashes():
    manifest = load_json("artifacts/solution_manifest.json")
    assert np.isclose(sum(manifest["weights"].values()), 1.0)
    assert manifest["production_status"] == "experiment_not_production_ready"
    for component in manifest["components"].values():
        path = (ROOT / component["path"]).resolve()
        assert path.exists()
        assert sha256(path.read_bytes()).hexdigest() == component["sha256"]


def test_reused_test_is_non_confirmatory_and_reproducible():
    result = load_json("artifacts/final_results.json")
    frame = pd.read_json(ROOT / "artifacts/reused_test_predictions.jsonl.gz", lines=True, compression="gzip")
    actual = metrics(frame["target"], frame["prediction"])
    assert len(frame) == 1000
    assert not result["test_used_for_selection"]
    for key in actual:
        assert np.isclose(actual[key], result["reused_test_non_confirmatory"][key], rtol=0, atol=1e-9)


def test_prediction_intervals_are_ordered():
    frame = pd.read_json(ROOT / "artifacts/reused_test_predictions.jsonl.gz", lines=True, compression="gzip")
    calibration = load_json("artifacts/calibration.json")
    assert calibration["levels"]["0.8"]["qhat_log"] <= calibration["levels"]["0.9"]["qhat_log"] <= calibration["levels"]["0.95"]["qhat_log"]
    for level in [80, 90, 95]:
        assert (frame[f"lower_{level}"] <= frame["prediction"]).all()
        assert (frame["prediction"] <= frame[f"upper_{level}"]).all()


def test_exported_artifacts_do_not_contain_sensitive_columns():
    forbidden = {"contact", "address", "asset_id", "report_id", "warehouse_id"}
    for name in ["history_features.jsonl.gz", "selected_oof_predictions.jsonl.gz", "reused_test_predictions.jsonl.gz"]:
        columns = set(pd.read_json(ROOT / "artifacts" / name, lines=True, compression="gzip", nrows=1).columns)
        assert not columns.intersection(forbidden)


def test_python_files_have_no_comments():
    paths = list((ROOT / "src").rglob("*.py")) + list((ROOT / "scripts").rglob("*.py")) + list((ROOT / "tests").rglob("*.py"))
    for path in paths:
        tokens = tokenize.generate_tokens(io.StringIO(path.read_text(encoding="utf-8")).readline)
        assert not any(token.type == tokenize.COMMENT for token in tokens)


def test_comparable_retrieval_is_asof_ranked_and_private():
    config = load_json("configs/experiments.json")
    target = {
        "as_of_date": "2025-07-15", "report_reference": "same_report", "district": "D", "ward_new": "W", "road": "R", "price_position": "VT2",
        "land_use": "Đất ở tại đô thị", "plot_shape": "Cân đối", "business_advantage": "Trung bình", "area_m2": 100.0, "frontage_m": 5.0,
        "length_m": 20.0, "distance_to_main_road_m": 100.0, "alley_width_m": 4.0,
    }
    common = {
        "Phân loại kho": "TSSS", "Diện tích (m2)": 100.0, "Giá giao dịch/rao bán (đ)": 10_000_000_000, "Giá ước tính (đ)": 9_500_000_000,
        "Thành phố/Quận/Huyện/Thị xã": "D", "Xã/Phường mới": "W", "Đường phố": "R", "Vị trí trong khung giá": "VT2", "Mục đích sử dụng đất": "Đất ở tại đô thị",
        "Hình dáng": "Cân đối", "Lợi thế kinh doanh": "Trung bình", "Kích thước mặt tiền (m)": 5.0, "Kích thước chiều dài": 20.0,
        "Khoảng cách đến đường chính (m)": 100.0, "Độ rộng ngõ/ngách nhỏ nhất (Từ đường chính đến BĐS)": 4.0, "Tình trạng giao dịch": "Chưa giao dịch",
        "Mã kho": "private-warehouse", "Mã tài sản": "private-asset", "Chi tiết": "private-detail", "Thông tin liên hệ": "private-contact",
    }
    rows = []
    for report, market_date, availability_date in [
        ("eligible_1", "10/07/2025", "11/07/2025"), ("eligible_2", "09/07/2025", "10/07/2025"), ("eligible_3", "08/07/2025", "09/07/2025"),
        ("same_report", "10/07/2025", "11/07/2025"), ("future_market", "15/07/2025", "14/07/2025"), ("future_availability", "10/07/2025", "15/07/2025"),
    ]:
        rows.append({**common, "Số báo cáo định giá": report, "Thời điểm giao dịch/rao bán (đ)": market_date, "Thời điểm hiệu lực": availability_date})
    output = retrieve_comparables([target], pd.DataFrame(rows), config, 3)[0]
    assert output["status"] == "automatic"
    assert output["returned_comparable_count"] == 3
    assert [item["comparable_reference"] for item in output["comparables"]] == ["TSSS-000002", "TSSS-000003", "TSSS-000004"]
    assert all(item["market_date"] < target["as_of_date"] for item in output["comparables"])
    rendered = json.dumps(output, ensure_ascii=False)
    assert "private-warehouse" not in rendered
    assert "private-asset" not in rendered
    assert "private-detail" not in rendered
    assert "private-contact" not in rendered


def test_comparable_retrieval_rejects_stale_dates_and_invalid_counts():
    config = load_json("configs/experiments.json")
    target = {
        "as_of_date": "2025-08-01", "district": "D", "ward_new": "W", "road": "R", "price_position": "VT2", "land_use": "Đất ở tại đô thị",
        "plot_shape": "Cân đối", "business_advantage": "Trung bình", "area_m2": 100.0, "frontage_m": 5.0, "length_m": 20.0,
        "distance_to_main_road_m": 100.0, "alley_width_m": 4.0,
    }
    output = retrieve_comparables([target], pd.DataFrame(), config, 3)[0]
    assert output["status"] == "reject"
    assert output["flags"] == ["unsupported_as_of_date"]
    try:
        retrieve_comparables([target], pd.DataFrame(), config, 2)
    except ValueError:
        return
    raise AssertionError("count outside 3-5 must be rejected")


def test_retrieval_quality_report_uses_asof_candidates_and_target_only_for_backtest():
    config = load_json("configs/experiments.json")
    base = pd.DataFrame({
        "source_excel_row": [2], "as_of_date": ["2025-07-15"], "district": ["d"], "ward_new": ["w"], "road": ["r"], "price_position": ["vt2"],
        "land_use": ["dat_o_do_thi"], "plot_shape": ["can_doi"], "business_advantage": ["trung_binh"], "area_m2": [100.0], "frontage_m": [5.0],
        "length_m": [20.0], "distance_to_main_road_m": [100.0], "alley_width_m": [4.0], "target_price_vnd_m2": [100_000_000.0],
    })
    target = {"Phân loại kho": "TSTĐ", "Số báo cáo định giá": "target_report"}
    candidate = {
        "Phân loại kho": "TSSS", "Số báo cáo định giá": "candidate_report", "Thời điểm giao dịch/rao bán (đ)": "10/07/2025", "Thời điểm hiệu lực": "11/07/2025",
        "Diện tích (m2)": 100.0, "Giá giao dịch/rao bán (đ)": 10_000_000_000, "Giá ước tính (đ)": 9_500_000_000, "Thành phố/Quận/Huyện/Thị xã": "d",
        "Xã/Phường mới": "w", "Đường phố": "r", "Vị trí trong khung giá": "vt2", "Mục đích sử dụng đất": "Đất ở tại đô thị", "Hình dáng": "Cân đối",
        "Lợi thế kinh doanh": "Trung bình", "Kích thước mặt tiền (m)": 5.0, "Kích thước chiều dài": 20.0, "Khoảng cách đến đường chính (m)": 100.0,
        "Độ rộng ngõ/ngách nhỏ nhất (Từ đường chính đến BĐS)": 4.0, "Tình trạng giao dịch": "Chưa giao dịch",
    }
    same_report = {**candidate, "Số báo cáo định giá": "target_report"}
    detail, report = build_retrieval_quality_report(base, pd.DataFrame([target, candidate, same_report]), config)
    assert detail.loc[0, "selected_count"] == 1
    assert detail.loc[0, "weighted_raw_prediction"] == 100_000_000.0
    assert report["coverage"]["coverage_rate"] == 1.0
    assert report["historical_price_backtest"]["weighted_raw_top_k"]["mape"] == 0.0
    assert "target_price_vnd_m2" not in report["leakage_guards"]


def test_retrieval_quality_artifacts_reproduce_and_are_private():
    report = load_json("artifacts/retrieval_quality_report.json")
    detail = pd.read_json(ROOT / "artifacts/retrieval_quality_rows.jsonl.gz", lines=True, compression="gzip")
    covered = detail.loc[detail["selected_count"].gt(0)]
    assert len(detail) == 7025
    assert len(covered) == report["coverage"]["rows_with_at_least_one_tsss"]
    actual = price_metrics(covered["target"], covered["weighted_estimated_prediction"])
    expected = report["historical_price_backtest"]["weighted_estimated_top_k"]
    for key in actual:
        assert np.isclose(actual[key], expected[key], rtol=0, atol=1e-9)
    forbidden = {"address", "contact", "asset_id", "report_id", "warehouse_id"}
    assert not forbidden.intersection(detail.columns)


def test_top_3_retrieval_quality_artifacts_reproduce():
    report = load_json("artifacts/retrieval_quality_report_k3.json")
    detail = pd.read_json(ROOT / "artifacts/retrieval_quality_rows_k3.jsonl.gz", lines=True, compression="gzip")
    covered = detail.loc[detail["selected_count"].gt(0)]
    actual = price_metrics(covered["target"], covered["weighted_estimated_prediction"])
    expected = report["historical_price_backtest"]["weighted_estimated_top_k"]
    assert report["scope"]["top_k"] == 3
    assert len(detail) == 7025
    for key in actual:
        assert np.isclose(actual[key], expected[key], rtol=0, atol=1e-9)


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    functions = [
        test_history_artifact_contract,
        test_history_uses_only_available_prior_labels,
        test_experiment_is_separate_from_frozen_branches,
        test_selected_oof_metrics_reproduce,
        test_selected_solution_improves_both_frozen_pipelines,
        test_solution_manifest_and_component_hashes,
        test_reused_test_is_non_confirmatory_and_reproducible,
        test_prediction_intervals_are_ordered,
        test_exported_artifacts_do_not_contain_sensitive_columns,
        test_python_files_have_no_comments,
        test_comparable_retrieval_is_asof_ranked_and_private,
        test_comparable_retrieval_rejects_stale_dates_and_invalid_counts,
        test_retrieval_quality_report_uses_asof_candidates_and_target_only_for_backtest,
        test_retrieval_quality_artifacts_reproduce_and_are_private,
        test_top_3_retrieval_quality_artifacts_reproduce,
    ]
    for function in functions:
        suite.addTest(unittest.FunctionTestCase(function))
    return suite
