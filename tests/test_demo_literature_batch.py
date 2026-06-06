import csv
import json
import unittest
from pathlib import Path


class DemoLiteratureBatchTest(unittest.TestCase):
    def setUp(self):
        self.demo_dir = Path("examples/demo_literature_batch")
        self.input_dir = self.demo_dir / "input_pdfs"
        self.csv_path = self.demo_dir / "expected_output.csv"
        self.xlsx_path = self.demo_dir / "expected_output.xlsx"
        self.fields_path = self.demo_dir / "fields.json"

    def test_demo_files_exist(self):
        self.assertTrue(self.demo_dir.is_dir())
        self.assertTrue(self.input_dir.is_dir())
        self.assertTrue(self.fields_path.is_file())
        self.assertTrue(self.csv_path.is_file())

        pdfs = [
            self.input_dir / "synthetic_catalysis_note_001.pdf",
            self.input_dir / "synthetic_catalysis_note_002.pdf",
        ]
        for pdf_path in pdfs:
            self.assertTrue(pdf_path.is_file())
            self.assertGreater(pdf_path.stat().st_size, 0)

    def test_fields_json_is_valid(self):
        fields = json.loads(self.fields_path.read_text(encoding="utf-8"))
        self.assertIsInstance(fields, list)
        self.assertGreaterEqual(len(fields), 1)

        labels = {field.get("label") for field in fields}
        expected_labels = {
            "source_file",
            "catalyst",
            "feedstock",
            "reaction_temperature",
            "reaction_pressure",
            "conversion",
            "selectivity",
            "main_product",
            "notes",
        }
        self.assertTrue(expected_labels.issubset(labels))

    def test_expected_output_csv_shape_and_safety(self):
        text = self.csv_path.read_text(encoding="utf-8")
        forbidden = [
            "DOI",
            "api_key",
            "sk-",
            "C:\\",
            "D:\\",
            "Users\\",
            "config.local.json",
        ]
        for token in forbidden:
            self.assertNotIn(token, text)

        with self.csv_path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

        required_headers = {
            "source_file",
            "catalyst",
            "feedstock",
            "reaction_temperature",
            "reaction_pressure",
            "conversion",
            "selectivity",
            "main_product",
            "notes",
        }
        self.assertTrue(required_headers.issubset(rows[0].keys()))
        self.assertGreaterEqual(len(rows), 2)
        self.assertTrue(all("Synthetic demo row only" in row["notes"] for row in rows))

    def test_expected_output_xlsx_exists_when_present(self):
        if self.xlsx_path.exists():
            self.assertGreater(self.xlsx_path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
