import csv
import tempfile
import unittest
from pathlib import Path

from chem_pdf_extractor.export import export_csv


class ExportTest(unittest.TestCase):
    def test_export_csv_removes_internal_metadata(self):
        rows = [
            {
                "paper_title": "Synthetic paper",
                "catalyst": "Ni/Al2O3",
                "source_path": "private/source.pdf",
                "llm_model": "hidden-model",
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "result.csv"
            export_csv(rows, output)
            with output.open("r", encoding="utf-8-sig", newline="") as handle:
                loaded = list(csv.DictReader(handle))

        self.assertEqual(loaded[0]["paper_title"], "Synthetic paper")
        self.assertEqual(loaded[0]["catalyst"], "Ni/Al2O3")
        self.assertNotIn("source_path", loaded[0])
        self.assertNotIn("llm_model", loaded[0])


if __name__ == "__main__":
    unittest.main()
