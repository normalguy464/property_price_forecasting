from pathlib import Path
import json
import sys
import tokenize
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from property_price_forecasting.audit import file_sha256


class StageOneAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PROJECT_ROOT.parent.parent / "Train_noi.xlsx"
        cls.profile_path = PROJECT_ROOT / "artifacts" / "stage_01" / "data_profile.json"
        cls.profile = json.loads(cls.profile_path.read_text(encoding="utf-8"))

    def test_source_snapshot(self):
        self.assertTrue(self.source.exists())
        self.assertEqual(self.profile["source"]["rows"], 34477)
        self.assertEqual(self.profile["source"]["columns"], 90)
        self.assertEqual(self.profile["source"]["sha256"], file_sha256(self.source))

    def test_schema_is_complete(self):
        self.assertEqual(len(self.profile["schema"]["column_names"]), 90)
        self.assertEqual(len(self.profile["schema"]["column_profiles"]), 90)
        self.assertEqual(len(set(self.profile["schema"]["column_names"])), 90)

    def test_temporal_scope(self):
        self.assertEqual(self.profile["time"]["month_count"], 17)
        self.assertEqual(self.profile["time"]["effective_date_parse_failures"], 0)
        self.assertEqual(self.profile["time"]["effective_month_year_mismatch_count"], 0)

    def test_privacy_guard(self):
        self.assertFalse(self.profile["privacy"]["sensitive_values_exported"])
        profiles = {item["name"]: item for item in self.profile["schema"]["column_profiles"]}
        for name in self.profile["privacy"]["sensitive_columns"]:
            self.assertNotIn("top_values", profiles[name])

    def test_python_files_have_no_comments(self):
        files = list((PROJECT_ROOT / "src").rglob("*.py")) + list((PROJECT_ROOT / "scripts").rglob("*.py")) + list((PROJECT_ROOT / "tests").rglob("*.py"))
        for path in files:
            with path.open("rb") as stream:
                tokens = tokenize.tokenize(stream.readline)
                comments = [token.string for token in tokens if token.type == tokenize.COMMENT]
            self.assertEqual(comments, [], str(path))


if __name__ == "__main__":
    unittest.main()
