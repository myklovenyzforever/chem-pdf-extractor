import unittest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from pydantic import Field, create_model

from chem_pdf_extractor import config
from chem_pdf_extractor.diagnostics import diagnostics_log_dir
from chem_pdf_extractor.extractor import JobState, run_extraction_job
from chem_pdf_extractor.pdf import list_pdf_files


def touch_pdf(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"%PDF-1.4\n% synthetic test pdf\n")


def minimal_runtime() -> config.RuntimeDeps:
    return config.RuntimeDeps(
        pd=pd,
        PdfReader=None,
        ChatPromptTemplate=None,
        ChatOllama=None,
        Field=Field,
        create_model=create_model,
    )


def assert_existing_paths_same(testcase: unittest.TestCase, actual: Path, expected: Path) -> None:
    actual = Path(actual)
    expected = Path(expected)
    if actual.exists() and expected.exists():
        testcase.assertTrue(actual.samefile(expected), f"{actual} != {expected}")
    else:
        testcase.assertEqual(actual, expected)


class PdfDiscoveryTest(unittest.TestCase):
    def test_default_input_dir_returns_project_input_pdfs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (
                patch("chem_pdf_extractor.config.PROJECT_ROOT", root),
                patch.dict(os.environ, {}, clear=True),
            ):
                result = config.default_input_dir()

        self.assertEqual(result, root / "input_pdfs")

    def test_default_input_dir_no_longer_returns_project_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (
                patch("chem_pdf_extractor.config.PROJECT_ROOT", root),
                patch.dict(os.environ, {}, clear=True),
            ):
                result = config.default_input_dir()

                self.assertNotEqual(result, root)
                self.assertTrue(result.exists())

    def test_default_output_path_preserves_source_checkout_file_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (
                patch("chem_pdf_extractor.config.PROJECT_ROOT", root),
                patch.dict(os.environ, {}, clear=True),
            ):
                result = config.default_output_path()

        self.assertEqual(result, root / config.OUTPUT_EXCEL_NAME)
        self.assertEqual(result.suffix.lower(), ".xlsx")

    def test_user_root_env_controls_default_input_output_and_runtime_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            user_root = Path(tmp)
            with patch.dict(os.environ, {"CHEM_PDF_EXTRACTOR_USER_ROOT": str(user_root)}, clear=False):
                expected_root = config.default_user_root()
                assert_existing_paths_same(self, expected_root, user_root)
                input_dir = config.default_input_dir()
                output_path = config.default_output_path()
                local_config = config.local_config_path()
                self.assertTrue(input_dir.exists())
                self.assertTrue(output_path.exists())

                self.assertEqual(input_dir, expected_root / "input_pdfs")
                self.assertEqual(output_path, expected_root / config.DEFAULT_OUTPUT_DIR_NAME)
                self.assertEqual(local_config, expected_root / ".runtime" / config.LOCAL_CONFIG_NAME)

    def test_user_root_env_controls_default_diagnostics_log_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            user_root = Path(tmp)
            with patch.dict(
                os.environ,
                {
                    "CHEM_PDF_EXTRACTOR_USER_ROOT": str(user_root),
                    "CHEM_PDF_EXTRACTOR_LOG_DIR": "",
                },
                clear=False,
            ):
                os.environ.pop("CHEM_PDF_EXTRACTOR_LOG_DIR", None)
                expected_root = config.default_user_root()
                assert_existing_paths_same(self, expected_root, user_root)
                log_dir = diagnostics_log_dir()

                self.assertEqual(log_dir, expected_root / "logs")
                self.assertTrue(log_dir.exists())

    def test_extractor_converts_user_root_output_directory_to_excel_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            user_root = Path(tmp)
            with patch.dict(os.environ, {"CHEM_PDF_EXTRACTOR_USER_ROOT": str(user_root)}, clear=False):
                input_dir = config.default_input_dir()
                output_dir = config.default_output_path()
                touch_pdf(input_dir / "source.pdf")
                state = JobState()
                with (
                    patch(
                        "chem_pdf_extractor.extractor.read_pdf_as_markdown_with_mode",
                        return_value=("Synthetic markdown", "pypdf_text"),
                    ),
                    patch(
                        "chem_pdf_extractor.extractor.extract_with_cloud_api",
                        return_value=[{"sample_id": "S-1"}],
                    ),
                ):
                    run_extraction_job(
                        {
                            "input_dir": str(input_dir),
                            "output_path": str(output_dir),
                            "recursive": False,
                            "llm_provider": "cloud",
                            "cloud_active": True,
                            "cloud_service_name": "cloud",
                            "cloud_model": "mock-model",
                            "cloud_api_key": "sk-test-not-real",
                            "pdf_mode": "pypdf_text",
                            "max_chars": 0,
                            "llm_timeout": 0,
                            "copy_failed_sources": False,
                            "translate_to_chinese": False,
                            "bad_row_min_fill_percent": 40,
                            "fields": [
                                {
                                    "label": "sample_id",
                                    "requirement": "required",
                                    "description": "Synthetic sample id.",
                                }
                            ],
                        },
                        minimal_runtime(),
                        state,
                    )

        snapshot = state.snapshot()
        self.assertEqual(Path(snapshot["output_path"]), output_dir / config.OUTPUT_EXCEL_NAME)
        self.assertEqual(Path(snapshot["partial_jsonl_path"]), output_dir / config.PARTIAL_JSONL_NAME)
        self.assertEqual(snapshot["failed"], 0)
        self.assertEqual(snapshot["success"], 1)

    def test_list_pdf_files_excludes_mineru_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            touch_pdf(root / "input_pdfs" / "source.pdf")
            touch_pdf(root / ".mineru_outputs" / "job-1" / "output" / "generated.pdf")

            with patch("chem_pdf_extractor.pdf.PROJECT_ROOT", root):
                files = list_pdf_files(root, recursive=True)

        self.assertEqual([path.name for path in files], ["source.pdf"])

    def test_list_pdf_files_excludes_examples_when_scanning_project_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            touch_pdf(root / "input_pdfs" / "user-source.pdf")
            touch_pdf(root / "examples" / "demo_literature_batch" / "input_pdfs" / "demo.pdf")

            with patch("chem_pdf_extractor.pdf.PROJECT_ROOT", root):
                files = list_pdf_files(root, recursive=True)

        self.assertEqual([path.name for path in files], ["user-source.pdf"])

    def test_list_pdf_files_still_finds_normal_pdfs_under_input_pdfs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "input_pdfs"
            touch_pdf(input_dir / "direct.pdf")
            touch_pdf(input_dir / "nested" / "nested.pdf")

            files = list_pdf_files(input_dir, recursive=True)

        self.assertEqual([path.name for path in files], ["direct.pdf", "nested.pdf"])

    def test_list_pdf_files_preserves_explicit_examples_input_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            demo_dir = root / "examples" / "demo_literature_batch" / "input_pdfs"
            touch_pdf(demo_dir / "demo.pdf")

            with patch("chem_pdf_extractor.pdf.PROJECT_ROOT", root):
                files = list_pdf_files(demo_dir, recursive=True)

        self.assertEqual([path.name for path in files], ["demo.pdf"])

    def test_non_recursive_mode_only_lists_direct_pdfs(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_dir = Path(tmp) / "input_pdfs"
            touch_pdf(input_dir / "direct.pdf")
            touch_pdf(input_dir / "nested" / "nested.pdf")

            files = list_pdf_files(input_dir, recursive=False)

        self.assertEqual([path.name for path in files], ["direct.pdf"])


if __name__ == "__main__":
    unittest.main()
