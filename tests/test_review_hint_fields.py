import csv
import tempfile
import unittest
from pathlib import Path

import pandas as pd
from pydantic import Field, create_model

from chem_pdf_extractor.config import (
    EXPORT_EXCLUDED_COLUMNS,
    REVIEW_AID_FIELD_LABELS,
    RuntimeDeps,
    append_review_aid_fields,
    build_dynamic_model,
    normalize_fields,
)
from chem_pdf_extractor.export import export_csv, export_excel
from chem_pdf_extractor.quality import row_is_bad_data


def minimal_runtime() -> RuntimeDeps:
    return RuntimeDeps(
        pd=pd,
        PdfReader=None,
        ChatPromptTemplate=None,
        ChatOllama=None,
        Field=Field,
        create_model=create_model,
    )


class ReviewHintFieldsTest(unittest.TestCase):
    def test_append_review_aid_fields_adds_expected_fields(self):
        fields = [{"label": "catalyst", "requirement": "required", "description": "Catalyst"}]

        result = append_review_aid_fields(fields)

        labels = [item["label"] for item in result]
        self.assertEqual(labels[0], "catalyst")
        self.assertEqual(labels[-4:], REVIEW_AID_FIELD_LABELS)
        for item in result[-4:]:
            self.assertEqual(item["requirement"], "optional")

    def test_append_review_aid_fields_does_not_duplicate_existing_labels(self):
        fields = [
            {"label": "source_evidence", "requirement": "required", "description": "User evidence"},
            {"label": "catalyst", "requirement": "required", "description": "Catalyst"},
        ]

        result = append_review_aid_fields(fields)
        labels = [item["label"] for item in result]

        self.assertEqual(labels.count("source_evidence"), 1)
        self.assertEqual(labels[-4:], REVIEW_AID_FIELD_LABELS)
        self.assertEqual(result[-4]["requirement"], "optional")

    def test_review_aid_fields_can_build_dynamic_model(self):
        user_fields = normalize_fields(
            [{"label": "catalyst", "requirement": "required", "description": "Catalyst"}]
        )
        model_fields = append_review_aid_fields(user_fields)

        _, key_to_label = build_dynamic_model(model_fields, minimal_runtime())

        labels = set(key_to_label.values())
        for label in REVIEW_AID_FIELD_LABELS:
            self.assertIn(label, labels)

    def test_review_aid_fields_are_not_export_excluded(self):
        for label in REVIEW_AID_FIELD_LABELS:
            self.assertNotIn(label, EXPORT_EXCLUDED_COLUMNS)

    def test_export_excel_keeps_review_hint_columns_at_end(self):
        rows = [
            {
                "catalyst": "Cat-A",
                "temperature": "300",
                "source_evidence": "Table 1 Cat-A",
                "source_hint": "table",
                "verification_status": "direct_text_match",
                "review_note": "Check table row.",
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "result.xlsx"
            export_excel(rows, output, minimal_runtime())
            dataframe = pd.read_excel(output, keep_default_na=False)

        self.assertEqual(list(dataframe.columns)[-4:], REVIEW_AID_FIELD_LABELS)
        self.assertEqual(dataframe.loc[0, "source_evidence"], "Table 1 Cat-A")
        self.assertEqual(dataframe.loc[0, "verification_status"], "direct_text_match")

    def test_export_csv_keeps_review_hint_columns_at_end(self):
        rows = [
            {
                "catalyst": "Cat-A",
                "temperature": "300",
                "source_evidence": "Table 1 Cat-A",
                "source_hint": "table",
                "verification_status": "direct_text_match",
                "review_note": "Check table row.",
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "result.csv"
            export_csv(rows, output)
            with output.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                loaded = list(reader)
                fieldnames = reader.fieldnames or []

        self.assertEqual(fieldnames[-4:], REVIEW_AID_FIELD_LABELS)
        self.assertEqual(loaded[0]["source_evidence"], "Table 1 Cat-A")
        self.assertEqual(loaded[0]["verification_status"], "direct_text_match")

    def test_export_rows_fill_missing_review_hint_columns(self):
        rows = [{"catalyst": "Cat-A"}]

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "result.csv"
            export_csv(rows, output)
            with output.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                loaded = list(reader)
                fieldnames = reader.fieldnames or []

        self.assertEqual(fieldnames[-4:], REVIEW_AID_FIELD_LABELS)
        for label in REVIEW_AID_FIELD_LABELS:
            self.assertEqual(loaded[0][label], "")

    def test_quality_filter_not_penalized_by_review_fields(self):
        fields = append_review_aid_fields(
            [
                {"label": "paper_title", "requirement": "required", "description": "Title"},
                {"label": "catalyst", "requirement": "required", "description": "Catalyst"},
            ]
        )
        row = {
            "paper_title": "Demo",
            "catalyst": "Cat-A",
            "source_evidence": "",
            "source_hint": "",
            "verification_status": "",
            "review_note": "",
        }

        self.assertFalse(row_is_bad_data(row, fields, min_fill_rate=0.4))


if __name__ == "__main__":
    unittest.main()
