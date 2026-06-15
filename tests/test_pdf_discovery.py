import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from chem_pdf_extractor import config
from chem_pdf_extractor.pdf import list_pdf_files


def touch_pdf(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"%PDF-1.4\n% synthetic test pdf\n")


class PdfDiscoveryTest(unittest.TestCase):
    def test_default_input_dir_returns_project_input_pdfs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("chem_pdf_extractor.config.PROJECT_ROOT", root):
                result = config.default_input_dir()

        self.assertEqual(result, root / "input_pdfs")

    def test_default_input_dir_no_longer_returns_project_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch("chem_pdf_extractor.config.PROJECT_ROOT", root):
                result = config.default_input_dir()

                self.assertNotEqual(result, root)
                self.assertTrue(result.exists())

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
