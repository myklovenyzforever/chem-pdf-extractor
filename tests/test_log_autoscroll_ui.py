import unittest
from pathlib import Path


TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "chem_pdf_extractor" / "templates" / "index.html"


class LogAutoScrollUiTest(unittest.TestCase):
    def read_template(self) -> str:
        return TEMPLATE_PATH.read_text(encoding="utf-8")

    def test_log_panel_uses_update_function(self):
        template = self.read_template()

        self.assertIn("function updateLogPanel", template)
        self.assertIn("updateLogPanel(data.logs || [])", template)

    def test_log_panel_preserves_manual_scroll(self):
        template = self.read_template()

        self.assertIn("wasNearBottom", template)
        self.assertIn("logsEl.scrollTop + logsEl.clientHeight", template)
        self.assertIn("logsEl.scrollHeight - 24", template)

    def test_log_panel_avoids_unnecessary_text_reset(self):
        template = self.read_template()

        self.assertIn("logsEl.textContent !== nextText", template)
        self.assertNotIn('document.getElementById("logs").textContent =', template)

    def test_log_panel_scrolls_when_empty_or_near_bottom(self):
        template = self.read_template()

        self.assertIn("wasEmpty", template)
        self.assertIn("logsEl.scrollTop = logsEl.scrollHeight", template)
        self.assertIn("if (wasEmpty || wasNearBottom)", template)


if __name__ == "__main__":
    unittest.main()
