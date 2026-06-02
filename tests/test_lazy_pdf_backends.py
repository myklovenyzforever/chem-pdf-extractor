import importlib
import sys
import unittest
from pathlib import Path

from chem_pdf_extractor.config import RuntimeDeps
from chem_pdf_extractor.pdf import read_pdf_as_markdown_with_mode


class LazyPdfBackendTest(unittest.TestCase):
    def test_module_imports_do_not_load_optional_pdf_backends(self):
        sys.modules.pop("pymupdf4llm", None)
        sys.modules.pop("pymupdf", None)
        sys.modules.pop("fitz", None)

        importlib.import_module("chem_pdf_extractor.config")
        importlib.import_module("chem_pdf_extractor.app")

        self.assertNotIn("pymupdf4llm", sys.modules)
        self.assertNotIn("pymupdf", sys.modules)
        self.assertNotIn("fitz", sys.modules)

    def test_core_dependency_checks_ignore_broken_optional_backends(self):
        config = importlib.import_module("chem_pdf_extractor.config")
        original_import_module = config.importlib.import_module

        def guarded_import(name, *args, **kwargs):
            if name in {"pymupdf4llm", "pymupdf", "fitz"}:
                raise OSError("simulated optional backend import failure")
            return original_import_module(name, *args, **kwargs)

        config.importlib.import_module = guarded_import
        try:
            missing = config.find_missing_imports()
        finally:
            config.importlib.import_module = original_import_module

        self.assertNotIn("pymupdf4llm", missing)
        self.assertNotIn("pymupdf", missing)
        runtime = RuntimeDeps(
            pd=None,
            PdfReader=None,
            ChatPromptTemplate=None,
            ChatOllama=None,
            Field=None,
            create_model=None,
        )
        self.assertIsNone(runtime.pymupdf4llm)
        self.assertIsNone(runtime.pymupdf)

    def test_pypdf_text_mode_does_not_use_optional_backends(self):
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
        self.assertIsNone(runtime.pymupdf4llm)
        self.assertIsNone(runtime.pymupdf)


if __name__ == "__main__":
    unittest.main()
