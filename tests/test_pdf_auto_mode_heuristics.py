import unittest
from pathlib import Path
from unittest.mock import patch

from chem_pdf_extractor.config import RuntimeDeps
from chem_pdf_extractor.pdf import markdown_needs_mineru, read_pdf_as_markdown_with_mode


def minimal_runtime_with_pymupdf4llm(markdown: str) -> RuntimeDeps:
    class FakePymupdf4llm:
        def to_markdown(self, _path):
            return markdown

    return RuntimeDeps(
        pd=None,
        PdfReader=None,
        ChatPromptTemplate=None,
        ChatOllama=None,
        Field=None,
        create_model=None,
        pymupdf4llm=FakePymupdf4llm(),
    )


class PdfAutoModeHeuristicsTest(unittest.TestCase):
    def test_short_markdown_triggers_mineru_recommendation(self):
        self.assertTrue(markdown_needs_mineru("Short extracted text."))

    def test_table_mentions_without_table_lines_trigger_mineru_recommendation(self):
        markdown = (
            "This synthetic extraction mentions Table 1 and Table 2 several times. "
            "The converted text contains paragraph references but no markdown table rows. "
        ) * 12

        self.assertTrue(markdown_needs_mineru(markdown))

    def test_adequate_markdown_keeps_pymupdf4llm_result(self):
        table_rows = "\n".join(
            [
                "| catalyst | temperature | conversion |",
                "| Cat-A | 320 C | 91% |",
                "| Cat-B | 300 C | 88% |",
            ]
        )
        markdown = ("Synthetic results text with enough content. " * 80) + "\n" + table_rows
        runtime = minimal_runtime_with_pymupdf4llm(markdown)

        with patch("chem_pdf_extractor.pdf.run_mineru_to_markdown") as mineru_mock:
            output, mode = read_pdf_as_markdown_with_mode(Path("synthetic.pdf"), "auto", runtime)

        self.assertEqual(mode, "pymupdf4llm")
        self.assertEqual(output, markdown)
        mineru_mock.assert_not_called()

    def test_auto_mode_tries_mineru_when_fast_markdown_needs_it_without_requiring_mineru_in_ci(self):
        runtime = minimal_runtime_with_pymupdf4llm("too short")

        with patch("chem_pdf_extractor.pdf.run_mineru_to_markdown", return_value="mineru markdown") as mineru_mock:
            output, mode = read_pdf_as_markdown_with_mode(Path("synthetic.pdf"), "auto", runtime)

        self.assertEqual(mode, "mineru")
        self.assertEqual(output, "mineru markdown")
        mineru_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
