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
from property_price_forecasting_wape.history_features import build_history_features


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
    ]
    for function in functions:
        suite.addTest(unittest.FunctionTestCase(function))
    return suite
