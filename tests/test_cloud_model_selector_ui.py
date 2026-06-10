import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = REPO_ROOT / "chem_pdf_extractor" / "templates" / "index.html"


class CloudModelSelectorUiTest(unittest.TestCase):
    def test_cloud_model_selector_uses_select_with_manual_fallback(self):
        template = TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn('id="cloudModelSelect"', template)
        self.assertIn('id="cloudModelCustom"', template)
        self.assertIn('id="cloudModel" type="hidden"', template)
        self.assertIn('value = "__manual__"', template)
        self.assertIn('manual_model_option', template)
        self.assertNotIn("cloudModelOptions", template)
        self.assertNotIn("<datalist", template)

    def test_cloud_model_value_is_used_for_save_and_start_payloads(self):
        template = TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn("function getCloudModelValue()", template)
        self.assertIn("model: getCloudModelValue()", template)
        self.assertIn("cloud_model: getCloudModelValue()", template)
        self.assertIn("syncCloudModelValue()", template)

    def test_service_name_is_advanced_and_defaults_in_javascript(self):
        template = TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn('<details class="advanced-config">', template)
        self.assertIn('function getCloudServiceName()', template)
        self.assertIn('return value || "openai_compatible";', template)
        self.assertIn("cloud_service_name: getCloudServiceName()", template)
        self.assertNotIn('LLM 服务名称</span> <span style="color:#d92d20">*</span>', template)

    def test_task_settings_layout_uses_responsive_grid_and_short_pdf_labels(self):
        template = TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn('class="task-grid"', template)
        self.assertIn('class="api-grid"', template)
        self.assertIn('data-i18n="pdf_mode_help"', template)
        self.assertIn('data-i18n="pdf_mode_mineru">MinerU</option>', template)


if __name__ == "__main__":
    unittest.main()
