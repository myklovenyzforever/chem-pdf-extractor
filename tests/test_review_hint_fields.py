import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from pydantic import Field, create_model

from chem_pdf_extractor.config import (
    EXPORT_EXCLUDED_COLUMNS,
    REVIEW_AID_FIELD_LABELS,
    RuntimeDeps,
    append_review_aid_fields,
    build_dynamic_model,
    field_instructions,
    normalize_fields,
)
from chem_pdf_extractor.export import export_csv, export_excel
from chem_pdf_extractor.llm import PROVENANCE_HINT_RULE, extract_with_cloud_api
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
    def review_tail(self, values):
        return values[-len(REVIEW_AID_FIELD_LABELS):]

    def test_append_review_aid_fields_adds_expected_fields(self):
        fields = [{"label": "catalyst", "requirement": "required", "description": "Catalyst"}]

        result = append_review_aid_fields(fields)

        labels = [item["label"] for item in result]
        self.assertEqual(labels[0], "catalyst")
        self.assertEqual(self.review_tail(labels), REVIEW_AID_FIELD_LABELS)
        for label in ("page_hint", "section_hint", "table_hint"):
            self.assertEqual(labels.count(label), 1)
        for item in self.review_tail(result):
            self.assertEqual(item["requirement"], "optional")
            self.assertIn("Do not invent", item["description"])

    def test_append_review_aid_fields_does_not_duplicate_existing_labels(self):
        fields = [
            {"label": "source_evidence", "requirement": "required", "description": "User evidence"},
            {"label": "page_hint", "requirement": "required", "description": "User page"},
            {"label": "catalyst", "requirement": "required", "description": "Catalyst"},
        ]

        result = append_review_aid_fields(fields)
        labels = [item["label"] for item in result]

        for label in REVIEW_AID_FIELD_LABELS:
            self.assertEqual(labels.count(label), 1)
        self.assertEqual(self.review_tail(labels), REVIEW_AID_FIELD_LABELS)
        for item in self.review_tail(result):
            self.assertEqual(item["requirement"], "optional")

    def test_review_aid_fields_can_build_dynamic_model(self):
        user_fields = normalize_fields(
            [{"label": "catalyst", "requirement": "required", "description": "Catalyst"}]
        )
        model_fields = append_review_aid_fields(user_fields)

        model, key_to_label = build_dynamic_model(model_fields, minimal_runtime())

        labels = set(key_to_label.values())
        for label in REVIEW_AID_FIELD_LABELS:
            self.assertIn(label, labels)
        schema_text = json.dumps(model.model_json_schema(), ensure_ascii=False)
        for label in ("page_hint", "section_hint", "table_hint"):
            self.assertIn(label, schema_text)
        self.assertIn("Do not invent", schema_text)

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
                "page_hint": "Page 3",
                "section_hint": "Results",
                "table_hint": "Table 1",
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "result.xlsx"
            export_excel(rows, output, minimal_runtime())
            dataframe = pd.read_excel(output, keep_default_na=False)

        self.assertEqual(self.review_tail(list(dataframe.columns)), REVIEW_AID_FIELD_LABELS)
        self.assertEqual(dataframe.loc[0, "source_evidence"], "Table 1 Cat-A")
        self.assertEqual(dataframe.loc[0, "page_hint"], "Page 3")
        self.assertEqual(dataframe.loc[0, "table_hint"], "Table 1")
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
                "page_hint": "Page 3",
                "section_hint": "Results",
                "table_hint": "Table 1",
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "result.csv"
            export_csv(rows, output)
            with output.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                loaded = list(reader)
                fieldnames = reader.fieldnames or []

        self.assertEqual(self.review_tail(fieldnames), REVIEW_AID_FIELD_LABELS)
        self.assertEqual(loaded[0]["source_evidence"], "Table 1 Cat-A")
        self.assertEqual(loaded[0]["page_hint"], "Page 3")
        self.assertEqual(loaded[0]["section_hint"], "Results")
        self.assertEqual(loaded[0]["table_hint"], "Table 1")
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

        self.assertEqual(self.review_tail(fieldnames), REVIEW_AID_FIELD_LABELS)
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
            "page_hint": "",
            "section_hint": "",
            "table_hint": "",
        }

        self.assertFalse(row_is_bad_data(row, fields, min_fill_rate=0.4))

    def test_prompt_and_cloud_schema_include_provenance_hints(self):
        fields = append_review_aid_fields(
            [{"label": "catalyst", "requirement": "required", "description": "Catalyst"}]
        )
        instructions = field_instructions(fields)
        for label in ("page_hint", "section_hint", "table_hint"):
            self.assertIn(label, instructions)
        self.assertIn("Do not invent page numbers", instructions)
        self.assertIn("Do not invent sections", instructions)
        self.assertIn("Do not invent table identifiers", instructions)

        _, key_to_label = build_dynamic_model(fields, minimal_runtime())
        captured_messages = []

        def fake_completion(_base_url, _api_key, _model, messages, _timeout):
            captured_messages.extend(messages)
            return '{"records":[{"field_01":"Cat-A"}]}'

        config = {
            "cloud_api_key": "sk-test-safe",
            "cloud_base_url": "https://api.example.test/v1",
            "cloud_model": "model",
            "llm_timeout": 0,
        }
        with patch("chem_pdf_extractor.llm.cloud_chat_completion", side_effect=fake_completion):
            extract_with_cloud_api(Path("paper.pdf"), config, fields, key_to_label, "Synthetic Page 3 Table 1")

        prompt_text = "\n".join(message["content"] for message in captured_messages)
        for label in ("page_hint", "section_hint", "table_hint"):
            self.assertIn(label, prompt_text)
        self.assertIn(PROVENANCE_HINT_RULE.strip(), prompt_text)


if __name__ == "__main__":
    unittest.main()
