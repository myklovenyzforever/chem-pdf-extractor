import tempfile
import unittest
from pathlib import Path

import pandas as pd

from chem_pdf_extractor.config import RuntimeDeps
from chem_pdf_extractor.export import append_jsonl, export_csv, export_excel, export_jsonl_excel
from chem_pdf_extractor.security import is_spreadsheet_formula_risk, sanitize_spreadsheet_cell


class SpreadsheetSanitizationTest(unittest.TestCase):
    def test_formula_risk_detection_and_sanitization(self):
        risky = [
            '=HYPERLINK("http://example.com","click")',
            "+SUM(1,2)",
            "-1+2",
            "@cmd",
            "\t=1+1",
            "＝+1",
        ]
        for value in risky:
            with self.subTest(value=value):
                self.assertTrue(is_spreadsheet_formula_risk(value))
                self.assertEqual("'" + value, sanitize_spreadsheet_cell(value))

        self.assertFalse(is_spreadsheet_formula_risk("normal text"))
        self.assertEqual("normal text", sanitize_spreadsheet_cell("normal text"))
        self.assertEqual("'=already safe", sanitize_spreadsheet_cell("'=already safe"))
        self.assertEqual(123, sanitize_spreadsheet_cell(123))

    def test_excel_export_escapes_formula_cells(self):
        runtime = RuntimeDeps(pd=pd, PdfReader=None, ChatPromptTemplate=None, ChatOllama=None, Field=None, create_model=None)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.xlsx"
            export_excel([{"catalyst": '=HYPERLINK("http://example.com","click")'}], path, runtime)
            frame = pd.read_excel(path)

        self.assertEqual('\'=HYPERLINK("http://example.com","click")', frame.loc[0, "catalyst"])

    def test_csv_export_escapes_formula_cells(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.csv"
            export_csv([{"catalyst": "+SUM(1,2)"}], path)
            text = path.read_text(encoding="utf-8-sig")

        self.assertIn("'+SUM(1,2)", text)

    def test_jsonl_to_excel_export_escapes_formula_cells(self):
        runtime = RuntimeDeps(pd=pd, PdfReader=None, ChatPromptTemplate=None, ChatOllama=None, Field=None, create_model=None)
        with tempfile.TemporaryDirectory() as tmp:
            jsonl = Path(tmp) / "rows.jsonl"
            xlsx = Path(tmp) / "rows.xlsx"
            append_jsonl(jsonl, {"note": "@cmd"})
            self.assertTrue(export_jsonl_excel(jsonl, xlsx, runtime))
            frame = pd.read_excel(xlsx)

        self.assertEqual("'@cmd", frame.loc[0, "note"])


if __name__ == "__main__":
    unittest.main()
