import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from chem_pdf_extractor.app import parse_args
from chem_pdf_extractor.config import DEFAULT_MAX_CHARS


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = REPO_ROOT / "chem_pdf_extractor" / "templates" / "index.html"
LAYOUT_CONTRACT_PATH = REPO_ROOT / "docs" / "ui_layout_contract.md"


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

    def test_default_max_chars_is_finite_and_cli_zero_remains_no_truncation(self):
        self.assertEqual(DEFAULT_MAX_CHARS, 80000)

        with patch.object(sys, "argv", ["chem-pdf-extractor"]):
            default_args = parse_args()
        self.assertEqual(default_args.max_chars, 80000)

        with patch.object(sys, "argv", ["chem-pdf-extractor", "--max-chars", "0"]):
            no_truncation_args = parse_args()
        self.assertEqual(no_truncation_args.max_chars, 0)

    def test_max_chars_help_keeps_manual_zero_and_presets_clear(self):
        en = i18n_block(self.template, "en")
        self.assertIn("0 = no truncation, may be slow/costly", en)
        self.assertIn("40k = small/cheap", en)
        self.assertIn("80k = recommended/default", en)
        self.assertIn("120k = larger context", en)
        self.assertIn("max_chars: \"Max chars\"", en)
        self.assertIn('max_chars: Number(document.getElementById("maxChars").value || 0)', self.template)

    def test_first_screen_workbench_required_controls_exist_before_fields(self):
        fields_panel_index = self.template.index('<section class="fields-panel">')
        required_ids = [
            "inputDir",
            "outputPath",
            "llmProvider",
            "pdfMode",
            "maxChars",
            "llmTimeout",
            "badRowMinFillPercent",
            "recursive",
            "autoFallback",
            "copyFailedSources",
            "startBtn",
            "pauseBtn",
            "resumeBtn",
            "stopBtn",
            "cloudPanel",
            "cloudBaseUrl",
            "cloudApiKey",
            "cloudModelSelect",
            "progressBar",
            "progressRatio",
            "done",
            "total",
            "success",
            "failed",
            "extractedRows",
            "successfulPdfs",
            "failedPdfs",
            "suspiciousBadRows",
            "cacheHits",
            "logs",
        ]

        for element_id in required_ids:
            marker = f'id="{element_id}"'
            with self.subTest(element_id=element_id):
                self.assertIn(marker, self.template)
                self.assertLess(self.template.index(marker), fields_panel_index)

    def test_compact_chinese_labels_are_layout_contract(self):
        zh = i18n_block(self.template, "zh")
        en = i18n_block(self.template, "en")
        compact_labels = {
            "llm_provider": "模型来源",
            "pdf_mode": "解析方式",
            "max_chars": "上传字数",
            "llm_timeout": "超时秒",
            "bad_row_percent": "坏行阈值",
            "ollama_url": "Ollama 地址",
            "recursive": "含子目录",
            "auto_fallback": "失败换模型",
            "copy_failed_sources": "复制失败 PDF",
            "copy_failed_sources_help": "会复制私有/版权 PDF，仅调试时开启。",
            "start": "开始",
            "pause": "暂停",
            "resume": "继续",
            "stop": "停止",
            "stat_suspicious_bad_rows": "可疑/坏行",
        }

        for key, label in compact_labels.items():
            with self.subTest(key=key):
                self.assertIn(f'{key}: "{label}"', zh)

        english_compact_labels = {
            "llm_provider": "LLM Provider",
            "pdf_mode": "PDF Mode",
            "max_chars": "Max chars",
            "llm_timeout": "Timeout",
            "bad_row_percent": "Bad row threshold",
            "ollama_url": "Ollama URL",
        }
        for key, label in english_compact_labels.items():
            with self.subTest(key=key):
                self.assertIn(f'{key}: "{label}"', en)

    def test_copy_failed_sources_is_not_enabled_by_default(self):
        start = self.template.index('id="copyFailedSources"')
        end = self.template.index("</label>", start)

        self.assertNotIn("checked", self.template[start:end])

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
        self.assertEqual(re.findall(r"<pre\b[^>]*>", self.template), ['<pre id="logs">'])

        for selector in [
            ".top-grid",
            ".left-stack",
            ".config-stack",
            ".stats-mount",
            ".task-panel",
            ".task-stats-panel",
            ".api-panel",
            "\n    .progress-panel",
            ".task-grid",
            ".api-grid",
            ".task-panel .checks",
            ".task-panel .actions",
            ".cloud-actions",
            ".status-box",
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

    def test_log_filter_buttons_are_vertically_centered(self):
        block = css_block(self.template, "\n    .log-filters button {")

        self.assertIn("display: inline-flex", block)
        self.assertIn("align-items: center", block)
        self.assertIn("justify-content: center", block)
        self.assertIn("height: 26px", block)
        self.assertIn("line-height: 1", block)

    def test_layout_contract_css_comment_points_to_docs(self):
        comment_index = self.template.index("UI layout contract")
        top_grid_index = self.template.index(".top-grid")

        self.assertLess(comment_index, top_grid_index)
        self.assertIn("1366x768 desktop workbench", self.template)
        self.assertIn("Only pre#logs may scroll internally", self.template)
        self.assertIn("fields", self.template[comment_index:top_grid_index])
        self.assertIn("panel intentionally remains below .top-grid", self.template)
        self.assertIn("docs/ui_layout_contract.md", self.template)

    def test_layout_contract_document_records_phase_one_rules(self):
        contract = LAYOUT_CONTRACT_PATH.read_text(encoding="utf-8")
        required_text = [
            "1366x768",
            "100% browser zoom",
            "compact three-column workbench",
            "Field editing intentionally stays below the first workbench",
            "No internal scrollbar in the left Task Settings column",
            "No internal scrollbar in the middle API/Progress or API/Statistics/Progress",
            "only intended internal scroll region in the workbench is `pre#logs`",
            "模型来源",
            "解析方式",
            "上传字数",
            "超时秒",
            "坏行阈值",
            "Ollama 地址",
            "复制失败 PDF",
            "Cloud mode shows Statistics under Task Settings",
            "Local Ollama mode shows Statistics above Progress",
            "Stat cards show number and label on the same row",
            "Copying failed source PDFs must not be enabled by default",
            "Start/Pause/Resume/Stop",
            "left and middle columns do not show internal scrollbars",
        ]

        for text in required_text:
            with self.subTest(text=text):
                self.assertIn(text, contract)

    def test_field_templates_replace_rows_after_confirmation(self):
        self.assertIn("const fieldTemplates = {", self.template)
        self.assertIn("function applyFieldTemplate()", self.template)
        self.assertIn('confirm(t("field_template_confirm"))', self.template)
        self.assertIn("replaceFields(fields)", self.template)


if __name__ == "__main__":
    unittest.main()
