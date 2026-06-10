import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = REPO_ROOT / "chem_pdf_extractor" / "templates" / "index.html"


def css_block(template: str, selector: str) -> str:
    start = template.index(selector)
    open_brace = template.index("{", start)
    close_brace = template.index("}", open_brace)
    return template[start: close_brace + 1]


class CloudModelSelectorUiTest(unittest.TestCase):
    def test_cloud_model_selector_uses_select_with_manual_fallback(self):
        template = TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn('id="cloudModelSelect"', template)
        self.assertIn('id="cloudModelCustom"', template)
        self.assertIn('id="cloudModel" type="hidden"', template)
        self.assertIn('value = "__manual__"', template)
        self.assertIn("manual_model_option", template)
        self.assertNotIn("cloudModelOptions", template)
        self.assertNotIn("<datalist", template)

    def test_cloud_model_value_is_used_for_save_and_start_payloads(self):
        template = TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn("function getCloudModelValue()", template)
        self.assertIn("model: getCloudModelValue()", template)
        self.assertIn("cloud_model: getCloudModelValue()", template)
        self.assertIn("syncCloudModelValue()", template)
        self.assertIn("async function loadCloudModels()", template)

    def test_service_name_is_advanced_and_defaults_in_javascript(self):
        template = TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn('<details class="advanced-config">', template)
        self.assertIn("function getCloudServiceName()", template)
        self.assertIn('return value || "openai_compatible";', template)
        self.assertIn("cloud_service_name: getCloudServiceName()", template)
        self.assertNotIn('LLM 服务名称</span> <span style="color:#d92d20">*</span>', template)

    def test_task_settings_layout_uses_responsive_grid_and_short_pdf_labels(self):
        template = TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn('class="task-grid"', template)
        self.assertIn('class="api-grid"', template)
        self.assertIn('data-i18n="pdf_mode_help"', template)
        self.assertIn('<div class="form-field full-span">', template)
        self.assertIn('data-i18n="pdf_mode_mineru">MinerU</option>', template)

    def test_workbench_layout_bounds_desktop_height_without_stretching_task_panel(self):
        template = TEMPLATE_PATH.read_text(encoding="utf-8")
        top_grid = css_block(template, ".top-grid")
        task_panel = css_block(template, ".task-panel")
        progress_panel = css_block(template, "\n    .progress-panel")

        self.assertIn("align-items: start", top_grid)
        self.assertIn("height: min(760px, calc(100vh - 24px))", top_grid)
        self.assertIn("overflow: hidden", top_grid)
        self.assertNotIn("align-items: stretch", top_grid)
        self.assertIn("flex: 0 0 auto", task_panel)
        self.assertIn("overflow: visible", task_panel)
        self.assertNotIn("flex: 1 1 0", task_panel)
        self.assertIn("flex: 0 0 auto", progress_panel)

    def test_log_panel_pre_scrolls_internally(self):
        template = TEMPLATE_PATH.read_text(encoding="utf-8")
        log_panel = css_block(template, ".log-panel")
        log_pre = css_block(template, ".log-panel pre")

        self.assertIn("height: 100%", log_panel)
        self.assertIn("overflow: hidden", log_panel)
        self.assertIn("flex: 1 1 auto", log_pre)
        self.assertIn("min-height: 0", log_pre)
        self.assertIn("height: auto", log_pre)
        self.assertIn("overflow: auto", log_pre)
        self.assertNotIn("height: 320px", log_pre)

    def test_narrow_layout_uses_auto_height_and_fixed_log_area(self):
        template = TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn(".top-grid { grid-template-columns: repeat(2, minmax(320px, 1fr)); height: auto; overflow: visible; }", template)
        self.assertIn(".log-panel { height: 360px; }", template)

    def test_cloud_mode_hides_only_ollama_fields(self):
        template = TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertIn("ollama-only", template)
        self.assertIn('document.querySelectorAll(".ollama-only")', template)
        self.assertIn("el.hidden = isCloud", template)
        self.assertIn('cloudPanel.style.display = isCloud ? "block" : "none"', template)
        self.assertIn('document.getElementById("autoFallback").disabled = isCloud', template)
        self.assertIn('<div class="form-field ollama-only">', template)
        self.assertIn('<div class="form-field full-span ollama-only">', template)

    def test_cloud_panel_removes_local_ollama_refresh_button(self):
        template = TEMPLATE_PATH.read_text(encoding="utf-8")

        self.assertNotIn("refreshModelsBtn", template)
        self.assertNotIn('onclick="loadModels()"', template)
        self.assertIn("async function loadModels()", template)
        self.assertIn("async function loadCloudModels()", template)


if __name__ == "__main__":
    unittest.main()
