import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from pydantic import Field, create_model

from chem_pdf_extractor.config import (
    BAD_ROWS_JSONL_NAME,
    CACHE_DIR_NAME,
    OUTPUT_EXCEL_NAME,
    PARTIAL_JSONL_NAME,
    SUSPICIOUS_ROWS_JSONL_NAME,
    RuntimeDeps,
)
from chem_pdf_extractor.export import load_jsonl_rows
from chem_pdf_extractor.extractor import JobState, run_extraction_job


def minimal_runtime() -> RuntimeDeps:
    return RuntimeDeps(
        pd=pd,
        PdfReader=None,
        ChatPromptTemplate=None,
        ChatOllama=None,
        Field=Field,
        create_model=create_model,
    )


class E2EMockWorkflowTest(unittest.TestCase):
    def make_config(self, root: Path) -> dict:
        input_dir = root / "input"
        output_dir = root / "output"
        input_dir.mkdir()
        output_dir.mkdir()
        (input_dir / "001-good.pdf").write_bytes(b"%PDF-1.4 synthetic good")
        (input_dir / "002-bad.pdf").write_bytes(b"%PDF-1.4 synthetic bad")
        return {
            "input_dir": str(input_dir),
            "output_path": str(output_dir),
            "llm_provider": "cloud",
            "cloud_active": True,
            "cloud_api_key": "sk-test-not-real-123456789",
            "cloud_base_url": "https://api.real-provider.test/v1",
            "cloud_model": "mock-model",
            "model": "mock-model",
            "pdf_mode": "pypdf_text",
            "max_chars": 0,
            "llm_timeout": 0,
            "recursive": False,
            "copy_failed_sources": False,
            "translate_to_chinese": False,
            "bad_row_min_fill_percent": 40,
            "fields": [
                {
                    "label": "催化剂",
                    "requirement": "required",
                    "description": "Catalyst or sample code.",
                },
                {
                    "label": "反应温度（℃）",
                    "requirement": "required",
                    "description": "Reaction temperature in Celsius.",
                },
                {
                    "label": "转化率（%）",
                    "requirement": "recommended",
                    "description": "Conversion percentage.",
                },
            ],
        }

    def test_mock_workflow_writes_outputs_flags_bad_and_suspicious_and_rerun_skips_processed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.make_config(root)
            output_dir = Path(config["output_path"])
            partial_path = output_dir / PARTIAL_JSONL_NAME
            output_excel = output_dir / OUTPUT_EXCEL_NAME
            bad_rows_path = output_dir / BAD_ROWS_JSONL_NAME
            suspicious_path = output_dir / SUSPICIOUS_ROWS_JSONL_NAME
            first_calls: list[str] = []
            second_calls: list[str] = []

            def fake_markdown(pdf_path, mode, runtime):
                return (f"Synthetic markdown for {pdf_path.name}", "pypdf_text")

            def first_extract(pdf_path, _config, _fields, _key_to_label, _markdown, quality_hint=""):
                first_calls.append(pdf_path.name)
                if pdf_path.name == "001-good.pdf":
                    return [{"催化剂": "Cat-A", "反应温度（℃）": "320", "转化率（%）": "125"}]
                return [{"催化剂": "", "反应温度（℃）": "", "转化率（%）": ""}]

            def second_extract(pdf_path, _config, _fields, _key_to_label, _markdown, quality_hint=""):
                second_calls.append(pdf_path.name)
                return [{"催化剂": "Cat-B", "反应温度（℃）": "280", "转化率（%）": "81"}]

            with (
                patch("urllib.request.urlopen", side_effect=AssertionError("network access is not allowed")),
                patch("chem_pdf_extractor.extractor.read_pdf_as_markdown_with_mode", side_effect=fake_markdown),
                patch("chem_pdf_extractor.extractor.extract_with_cloud_api", side_effect=first_extract),
            ):
                state = JobState()
                run_extraction_job(config, minimal_runtime(), state)

            snapshot = state.snapshot()
            self.assertFalse(snapshot["running"])
            self.assertEqual(snapshot["success"], 1)
            self.assertEqual(snapshot["failed"], 1)
            self.assertEqual(snapshot["done"], 2)
            self.assertEqual(first_calls, ["001-good.pdf", "002-bad.pdf", "002-bad.pdf"])
            self.assertTrue(partial_path.exists())
            self.assertTrue(output_excel.exists())
            self.assertEqual(len(load_jsonl_rows(partial_path)), 1)
            self.assertEqual(len(load_jsonl_rows(bad_rows_path)), 1)
            self.assertEqual(len(load_jsonl_rows(suspicious_path)), 1)
            first_row = load_jsonl_rows(partial_path)[0]
            self.assertEqual(first_row["催化剂"], "Cat-A")
            self.assertEqual(first_row["llm_provider"], "cloud")
            self.assertEqual(first_row["pdf_to_md_mode"], "pypdf_text")
            self.assertIn("source_path", first_row)

            cache_dir = Path(config["input_dir"]) / CACHE_DIR_NAME
            if cache_dir.exists():
                shutil.rmtree(cache_dir)

            with (
                patch("urllib.request.urlopen", side_effect=AssertionError("network access is not allowed")),
                patch("chem_pdf_extractor.extractor.read_pdf_as_markdown_with_mode", side_effect=fake_markdown),
                patch("chem_pdf_extractor.extractor.extract_with_cloud_api", side_effect=second_extract),
            ):
                rerun_state = JobState()
                run_extraction_job(config, minimal_runtime(), rerun_state)

            rerun_snapshot = rerun_state.snapshot()
            self.assertFalse(rerun_snapshot["running"])
            self.assertEqual(second_calls, ["002-bad.pdf"])
            self.assertEqual(rerun_snapshot["success"], 2)
            self.assertEqual(rerun_snapshot["failed"], 0)
            self.assertEqual(rerun_snapshot["done"], 2)
            self.assertEqual(len(load_jsonl_rows(partial_path)), 2)
            self.assertTrue(output_excel.exists())


if __name__ == "__main__":
    unittest.main()
