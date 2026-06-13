import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = REPO_ROOT / "chem_pdf_extractor" / "templates" / "index.html"


def css_block(template: str, selector: str) -> str:
    start = template.index(selector)
    open_brace = template.index("{", start)
    close_brace = template.index("}", open_brace)
    return template[start: close_brace + 1]


def i18n_block(template: str, lang: str) -> str:
    marker = f"{lang}: {{"
    start = template.index(marker)
    if lang == "zh":
        end = template.index("      en: {", start)
    else:
        end = template.index("    };", start)
    return template[start:end]


class CompactUiGuidanceTest(unittest.TestCase):
    def setUp(self):
        self.template = TEMPLATE_PATH.read_text(encoding="utf-8")

    def test_new_ui_controls_exist(self):
        checks = [
            'class="workflow-guide"',
            'id="pdfModeHelp"',
            'setMaxCharsPreset(40000)',
            'setMaxCharsPreset(80000)',
            'setMaxCharsPreset(120000)',
            'id="testCloudApiBtn"',
            'id="cloudTestStatus" class="field-help cloud-test-status" aria-live="polite"',
            'id="nextAction" class="status-line" aria-live="polite"',
            'data-log-filter="all"',
            'data-log-filter="success"',
            'data-log-filter="warning"',
            'data-log-filter="error"',
            'data-log-filter="api"',
            'data-log-filter="paths"',
            'id="fieldTemplateSelect"',
            'id="applyFieldTemplateBtn"',
        ]
        for text in checks:
            with self.subTest(text=text):
                self.assertIn(text, self.template)

    def test_new_i18n_keys_exist_for_zh_and_en(self):
        keys = [
            "guide_api",
            "guide_folder",
            "guide_pdf_mode",
            "guide_test",
            "guide_review",
            "pdf_mode_help_pymupdf4llm",
            "pdf_mode_help_mineru",
            "pdf_mode_help_pypdf_text",
            "pdf_mode_help_auto",
            "pdf_mode_help_pymupdf_text",
            "preset_40k",
            "preset_80k",
            "preset_120k",
            "max_chars_help",
            "test_api",
            "api_test_idle",
            "api_test_testing",
            "api_test_success",
            "api_test_partial",
            "api_test_failed",
            "alert_fill_cloud_test",
            "next_action_waiting",
            "next_action_running",
            "next_action_paused",
            "next_action_done",
            "next_action_done_failed",
            "next_action_review_rows",
            "log_filter_all",
            "log_filter_success",
            "log_filter_warning",
            "log_filter_error",
            "log_filter_api",
            "log_filter_paths",
            "field_template",
            "template_current_default",
            "template_catalysis",
            "template_materials",
            "template_environmental",
            "template_electrochemistry",
            "apply_template",
            "field_template_confirm",
        ]
        for lang in ["zh", "en"]:
            block = i18n_block(self.template, lang)
            for key in keys:
                with self.subTest(lang=lang, key=key):
                    self.assertIn(f"{key}:", block)

    def test_cloud_api_test_frontend_uses_protected_endpoint(self):
        self.assertIn('apiFetch("/api/cloud-test"', self.template)
        self.assertIn("async function testCloudApi()", self.template)
        self.assertIn("setCloudTestStatus", self.template)
        self.assertNotIn("alert(t(\"api_test_success", self.template)

    def test_field_panel_remains_below_main_workbench(self):
        top_grid_index = self.template.index('<div class="top-grid">')
        log_panel_index = self.template.index('<section class="log-panel">')
        fields_panel_index = self.template.index('<section class="fields-panel">')

        self.assertLess(top_grid_index, log_panel_index)
        self.assertLess(log_panel_index, fields_panel_index)
        self.assertIn('</div>\n\n        <section class="fields-panel">', self.template)

    def test_only_logs_pre_has_first_workbench_internal_scroll_target(self):
        for selector in [
            ".top-grid",
            ".left-stack",
            ".config-stack",
            ".task-panel",
            ".task-stats-panel",
            ".api-panel",
            "\n    .progress-panel",
            ".log-filters",
            ".workflow-guide",
        ]:
            block = css_block(self.template, selector)
            with self.subTest(selector=selector):
                self.assertNotIn("overflow: auto", block)
                self.assertNotIn("overflow-y: auto", block)
                self.assertNotIn("overflow: scroll", block)
                self.assertNotIn("overflow-y: scroll", block)

        log_pre = css_block(self.template, ".log-panel pre")
        self.assertIn("overflow: auto", log_pre)

    def test_field_templates_replace_rows_after_confirmation(self):
        self.assertIn("const fieldTemplates = {", self.template)
        self.assertIn("function applyFieldTemplate()", self.template)
        self.assertIn('confirm(t("field_template_confirm"))', self.template)
        self.assertIn("replaceFields(fields)", self.template)


if __name__ == "__main__":
    unittest.main()
