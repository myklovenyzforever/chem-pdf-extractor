import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from chem_pdf_extractor.diagnostics import (
    append_diagnostic_log,
    diagnostic_log_path,
    diagnostics_log_dir,
    log_exception,
    log_process_exit,
    log_startup_event,
)
from chem_pdf_extractor.extractor import JobState


class DiagnosticsLoggingTest(unittest.TestCase):
    def test_diagnostic_log_dir_respects_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"CHEM_PDF_EXTRACTOR_LOG_DIR": tmp}):
                log_dir = diagnostics_log_dir()

            self.assertEqual(log_dir, Path(tmp))
            self.assertTrue(log_dir.exists())

    def test_append_diagnostic_log_writes_utf8_safe_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"CHEM_PDF_EXTRACTOR_LOG_DIR": tmp}):
                append_diagnostic_log("startup.log", "hello" + chr(0xD800))
                content = diagnostic_log_path("startup.log").read_text(encoding="utf-8")

        self.assertIn("hello", content)
        content.encode("utf-8")
        self.assertNotIn(chr(0xD800), content)

    def test_log_exception_writes_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"CHEM_PDF_EXTRACTOR_LOG_DIR": tmp}):
                try:
                    raise RuntimeError("boom")
                except RuntimeError as exc:
                    log_exception(exc, context="unit_test")
                content = diagnostic_log_path("crash.log").read_text(encoding="utf-8")

        self.assertIn("RuntimeError", content)
        self.assertIn("boom", content)
        self.assertIn("unit_test", content)

    def test_log_startup_event_redacts_api_key_like_arguments(self):
        argv = ["ShuJuTiQuJiaoBen.py", "--cloud-api-key", "sk-secret-value", "--port", "8766"]
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch.dict(os.environ, {"CHEM_PDF_EXTRACTOR_LOG_DIR": tmp}),
                patch("sys.argv", argv),
            ):
                log_startup_event("test")
                content = diagnostic_log_path("startup.log").read_text(encoding="utf-8")

        self.assertIn("--cloud-api-key", content)
        self.assertIn("<redacted>", content)
        self.assertNotIn("sk-secret-value", content)

    def test_job_state_add_log_persists_task_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"CHEM_PDF_EXTRACTOR_LOG_DIR": tmp}):
                state = JobState()
                state.add_log("test message")
                content = diagnostic_log_path("task.log").read_text(encoding="utf-8")

        self.assertIn("test message", content)

    def test_log_process_exit_writes_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"CHEM_PDF_EXTRACTOR_LOG_DIR": tmp}):
                log_process_exit(1)
                content = diagnostic_log_path("startup.log").read_text(encoding="utf-8")

        self.assertIn("process exited", content)
        self.assertIn("exit code", content)
        self.assertIn("1", content)

    def test_bat_mentions_logs_and_exit_code(self):
        content = Path("YiJianQiDong.bat").read_text(encoding="utf-8")

        self.assertIn("logs", content)
        self.assertIn("startup.log", content)
        self.assertIn("crash.log", content)
        self.assertIn("task.log", content)
        self.assertIn("ERRORLEVEL", content)
        self.assertIn("pause", content.lower())

    def test_gitignore_ignores_logs_directory(self):
        content = Path(".gitignore").read_text(encoding="utf-8")

        self.assertIn("logs/", content)


if __name__ == "__main__":
    unittest.main()
