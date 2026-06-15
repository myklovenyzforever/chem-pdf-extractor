import unittest
from pathlib import Path
from unittest.mock import patch

from chem_pdf_extractor.llm import (
    CloudStructuredOutputError,
    MALFORMED_JSON_WARNING,
    MISSING_RECORDS_WARNING,
    NON_OBJECT_RECORD_WARNING,
    RECORDS_NOT_LIST_WARNING,
    SINGLE_OBJECT_FALLBACK_WARNING,
    TOP_LEVEL_NOT_OBJECT_WARNING,
    TYPE_NORMALIZATION_FAILED_WARNING,
    UNKNOWN_KEYS_WARNING,
    labeled_rows_with_report,
    parse_cloud_extraction_payload,
    extract_with_cloud_api,
)


def sample_fields():
    return [
        {"label": "catalyst", "type": "str", "requirement": "required", "description": "Catalyst"},
        {"label": "temperature", "type": "float", "requirement": "recommended", "description": "Temperature"},
        {"label": "notes", "type": "str", "requirement": "optional", "description": "Notes"},
    ]


def sample_key_to_label(fields):
    return {f"field_{index:02d}": item["label"] for index, item in enumerate(fields, start=1)}


def normalize(raw):
    fields = sample_fields()
    return labeled_rows_with_report(raw, fields, sample_key_to_label(fields))


class CloudStructuredOutputValidationTest(unittest.TestCase):
    def test_valid_records_list_normalizes_requested_fields(self):
        rows, report = normalize(
            {"records": [{"field_01": "Cat-A", "field_02": "320.5", "field_03": "Table row"}]}
        )

        self.assertEqual(rows, [{"catalyst": "Cat-A", "temperature": 320.5, "notes": "Table row"}])
        self.assertEqual(report.warnings, [])
        self.assertEqual(report.normalized_record_count, 1)

    def test_single_object_fallback_is_reported(self):
        rows, report = normalize({"field_01": "Cat-A", "field_02": "300"})

        self.assertEqual(rows[0]["catalyst"], "Cat-A")
        self.assertEqual(rows[0]["temperature"], 300.0)
        self.assertEqual(rows[0]["notes"], "")
        self.assertIn(SINGLE_OBJECT_FALLBACK_WARNING, report.warnings)

    def test_missing_records_returns_blank_row_with_warning(self):
        rows, report = normalize({"result": "no records here"})

        self.assertEqual(rows, [{"catalyst": "", "temperature": "", "notes": ""}])
        self.assertIn(MISSING_RECORDS_WARNING, report.warnings)

    def test_records_value_must_be_list(self):
        rows, report = normalize({"records": {"field_01": "Cat-A"}})

        self.assertEqual(rows, [{"catalyst": "", "temperature": "", "notes": ""}])
        self.assertIn(RECORDS_NOT_LIST_WARNING, report.warnings)

    def test_non_object_records_are_dropped_and_reported(self):
        rows, report = normalize({"records": [{"field_01": "Cat-A"}, "bad", 7]})

        self.assertEqual(rows[0]["catalyst"], "Cat-A")
        self.assertEqual(report.dropped_record_count, 2)
        self.assertIn(NON_OBJECT_RECORD_WARNING, report.warnings)

    def test_unknown_keys_do_not_crash_and_are_reported(self):
        rows, report = normalize({"records": [{"field_01": "Cat-A", "extra": "ignored", "field_99": "ignored"}]})

        self.assertEqual(rows[0]["catalyst"], "Cat-A")
        self.assertIn(UNKNOWN_KEYS_WARNING, report.warnings)
        self.assertEqual(report.unknown_keys, ["extra", "field_99"])

    def test_missing_requested_fields_become_empty_strings(self):
        rows, report = normalize({"records": [{"field_01": "Cat-A"}]})

        self.assertEqual(rows[0], {"catalyst": "Cat-A", "temperature": "", "notes": ""})
        self.assertNotIn(TYPE_NORMALIZATION_FAILED_WARNING, report.warnings)

    def test_invalid_and_nested_values_are_normalized_safely(self):
        rows, report = normalize(
            {
                "records": [
                    {
                        "field_01": {"name": "Cat-A", "grade": None},
                        "field_02": "not a number",
                        "field_03": {"source": "table", "row": 2},
                    }
                ]
            }
        )

        self.assertIn('"name": "Cat-A"', rows[0]["catalyst"])
        self.assertEqual(rows[0]["temperature"], "")
        self.assertIn('"source": "table"', rows[0]["notes"])
        self.assertIn(TYPE_NORMALIZATION_FAILED_WARNING, report.warnings)
        self.assertEqual(report.type_normalization_failed, ["field_02"])

    def test_parse_cloud_payload_rejects_malformed_json_without_response_text(self):
        private_text = "PRIVATE_PDF_TEXT_SHOULD_NOT_LEAK"
        model_response = f"FULL_MODEL_RESPONSE_SHOULD_NOT_LEAK {private_text}"

        with self.assertRaises(CloudStructuredOutputError) as ctx:
            parse_cloud_extraction_payload("not json " + model_response)

        message = str(ctx.exception)
        self.assertIn(MALFORMED_JSON_WARNING, message)
        self.assertNotIn(model_response, message)
        self.assertNotIn(private_text, message)

    def test_parse_cloud_payload_rejects_top_level_non_object(self):
        with self.assertRaises(CloudStructuredOutputError) as ctx:
            parse_cloud_extraction_payload('["not", "an", "object"]')

        self.assertIn(TOP_LEVEL_NOT_OBJECT_WARNING, str(ctx.exception))

    def test_extract_with_cloud_api_does_not_leak_prompt_response_pdf_text_or_key_on_malformed_json(self):
        api_key = "sk-test-secret-123456"
        private_pdf_text = "PRIVATE_PDF_TEXT_SHOULD_NOT_LEAK"
        full_response = "FULL_MODEL_RESPONSE_SHOULD_NOT_LEAK"
        full_prompt_marker = "FULL_PROMPT_SHOULD_NOT_LEAK"
        fields = sample_fields()
        config = {
            "cloud_api_key": api_key,
            "cloud_base_url": "https://api.example.test/v1",
            "cloud_model": "mock-model",
            "llm_timeout": 0,
        }

        with patch(
            "chem_pdf_extractor.llm.cloud_chat_completion",
            return_value=f"not-json {full_response} {private_pdf_text} {api_key}",
        ):
            with self.assertRaises(CloudStructuredOutputError) as ctx:
                extract_with_cloud_api(
                    Path("paper.pdf"),
                    config,
                    fields,
                    sample_key_to_label(fields),
                    f"{private_pdf_text} {full_prompt_marker}",
                )

        message = str(ctx.exception)
        self.assertIn(MALFORMED_JSON_WARNING, message)
        for forbidden in [api_key, private_pdf_text, full_response, full_prompt_marker]:
            self.assertNotIn(forbidden, message)


if __name__ == "__main__":
    unittest.main()
