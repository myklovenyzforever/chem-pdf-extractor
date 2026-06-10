import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from chem_pdf_extractor.app import parse_args
from chem_pdf_extractor.config import DEFAULT_PDF_MODE, PDF_MODE_CHOICES, RuntimeDeps
from chem_pdf_extractor.pdf import mineru_command_candidates, read_pdf_as_markdown_with_mode


class PdfModeTest(unittest.TestCase):
    def test_default_pdf_mode_is_pymupdf4llm(self):
        with patch.object(sys, "argv", ["chem-pdf-extractor"]):
            args = parse_args()

        self.assertEqual(DEFAULT_PDF_MODE, "pymupdf4llm")
        self.assertEqual(args.pdf_mode, "pymupdf4llm")

    def test_accepted_pdf_modes_include_mineru(self):
        self.assertIn("pypdf_text", PDF_MODE_CHOICES)
        self.assertIn("pymupdf4llm", PDF_MODE_CHOICES)
        self.assertIn("mineru", PDF_MODE_CHOICES)

        with patch.object(sys, "argv", ["chem-pdf-extractor", "--pdf-mode", "mineru"]):
            args = parse_args()

        self.assertEqual(args.pdf_mode, "mineru")

    def test_invalid_pdf_mode_fails_clearly(self):
        with patch.object(sys, "argv", ["chem-pdf-extractor", "--pdf-mode", "not-a-backend"]):
            with self.assertRaises(SystemExit):
                parse_args()

    def test_mineru_without_installed_backend_fails_clearly(self):
        runtime = RuntimeDeps(
            pd=None,
            PdfReader=None,
            ChatPromptTemplate=None,
            ChatOllama=None,
            Field=None,
            create_model=None,
        )

        with patch(
            "chem_pdf_extractor.pdf.mineru_command_candidates",
            return_value=[["definitely_missing_mineru_command_for_test"]],
        ):
            with self.assertRaisesRegex(RuntimeError, "MinerU PDF backend is optional"):
                read_pdf_as_markdown_with_mode(Path("dummy.pdf"), "mineru", runtime)

    def test_mineru_command_candidates_prefer_environment_command(self):
        with patch.dict("os.environ", {"MINERU_COMMAND": "custom-mineru --flag"}, clear=False):
            candidates = mineru_command_candidates()

        self.assertEqual(candidates[0], ["custom-mineru", "--flag"])

        def test_mineru_command_candidates_prefer_project_venv_mineru_exe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scripts_dir = root / ".venv" / "Scripts"
            scripts_dir.mkdir(parents=True)
            mineru_exe = scripts_dir / "mineru.exe"
            mineru_exe.write_text("", encoding="utf-8")
            python_exe = scripts_dir / "python.exe"

            with patch.dict("os.environ", {}, clear=True):
                with patch.object(sys, "executable", str(python_exe)):
                    with patch("chem_pdf_extractor.pdf.PROJECT_ROOT", root):
                        candidates = mineru_command_candidates()

        first = Path(candidates[0][0])
        self.assertEqual(first.name.lower(), "mineru.exe")
        self.assertEqual(first.parent.name.lower(), "scripts")
        self.assertEqual(first.parent.parent.name.lower(), ".venv")
        self.assertTrue(first.exists())
        self.assertTrue(first.samefile(mineru_exe))

        self.assertIn(["mineru"], candidates)
        self.assertIn(["magic-pdf"], candidates)
        self.assertLess(candidates.index(["mineru"]), candidates.index(["magic-pdf"]))

    def test_pypdf_text_existing_behavior_still_works(self):
        class FakePage:
            def extract_text(self):
                return "stable pypdf text"

        class FakePdfReader:
            def __init__(self, path, strict=False):
                self.path = path
                self.strict = strict
                self.pages = [FakePage()]

        runtime = RuntimeDeps(
            pd=None,
            PdfReader=FakePdfReader,
            ChatPromptTemplate=None,
            ChatOllama=None,
            Field=None,
            create_model=None,
        )

        markdown, mode = read_pdf_as_markdown_with_mode(Path("dummy.pdf"), "pypdf_text", runtime)

        self.assertEqual(mode, "pypdf_text")
        self.assertIn("stable pypdf text", markdown)


if __name__ == "__main__":
    unittest.main()
