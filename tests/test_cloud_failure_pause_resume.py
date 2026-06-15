import io
import json
import os
import tempfile
import threading
import time
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from pydantic import Field, create_model

from chem_pdf_extractor.config import (
    ERROR_STATS_JSONL_NAME,
    OUTPUT_EXCEL_NAME,
    PARTIAL_JSONL_NAME,
    RuntimeDeps,
    validate_cloud_start_config,
)
from chem_pdf_extractor.export import load_jsonl_rows
from chem_pdf_extractor.extractor import (
    RESUMABLE_CLOUD_PAUSE_REASON,
    JobState,
    run_extraction_job,
)
from chem_pdf_extractor.llm import (
    TransientCloudAPIError,
    cloud_chat_completion,
    is_transient_cloud_error,
)


def minimal_runtime() -> RuntimeDeps:
    return RuntimeDeps(
        pd=pd,
        PdfReader=None,
        ChatPromptTemplate=None,
        ChatOllama=None,
        Field=Field,
        create_model=create_model,
    )


def wait_until(predicate, *, timeout: float = 8.0, interval: float = 0.02) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return
        time.sleep(interval)
    raise AssertionError("Timed out waiting for expected state")


class CloudFailurePauseResumeTest(unittest.TestCase):
    def base_config(self, root: Path) -> dict:
        input_dir = root / "input"
        output_dir = root / "output"
        input_dir.mkdir()
        output_dir.mkdir()
        (input_dir / "001-success.pdf").write_bytes(b"%PDF-1.4 synthetic")
        (input_dir / "002-retry.pdf").write_bytes(b"%PDF-1.4 synthetic")
        return {
            "input_dir": str(input_dir),
            "output_path": str(output_dir),
            "llm_provider": "cloud",
            "cloud_active": True,
            "cloud_api_key": "sk-test-secret-123456789",
            "cloud_base_url": "https://api.real-provider.test/v1",
            "cloud_model": "test-model",
            "model": "test-model",
            "pdf_mode": "pypdf_text",
            "max_chars": 0,
            "llm_timeout": 0,
            "recursive": False,
            "copy_failed_sources": False,
            "translate_to_chinese": False,
            "bad_row_min_fill_percent": 40,
            "fields": [
                {
                    "label": "catalyst",
                    "requirement": "required",
                    "description": "Catalyst name",
                }
            ],
        }

    def test_transient_cloud_failure_pauses_then_resume_retries_current_pdf(self):
        secret = "sk-test-secret-123456789"
        private_text = "PRIVATE_PDF_TEXT_SHOULD_NOT_LEAK"
        prompt_text = "FULL_PROMPT_SHOULD_NOT_LEAK"
        response_text = "FULL_MODEL_RESPONSE_SHOULD_NOT_LEAK"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self.base_config(root)
            state = JobState()
            calls: list[str] = []
            output_path = Path(config["output_path"]) / OUTPUT_EXCEL_NAME
            partial_path = Path(config["output_path"]) / PARTIAL_JSONL_NAME
            error_stats_path = Path(config["output_path"]) / ERROR_STATS_JSONL_NAME
            log_dir = root / "logs"

            def fake_extract(pdf_path, _config, _fields, _key_to_label, _markdown, quality_hint=""):
                calls.append(pdf_path.name)
                if pdf_path.name == "002-retry.pdf" and calls.count(pdf_path.name) == 1:
                    raise TransientCloudAPIError(
                        f"timeout {secret} {private_text} {prompt_text} {response_text}"
                    )
                return [{"catalyst": f"Cat {pdf_path.stem}"}]

            with (
                patch.dict(os.environ, {"CHEM_PDF_EXTRACTOR_LOG_DIR": str(log_dir)}),
                patch(
                    "chem_pdf_extractor.extractor.read_pdf_as_markdown_with_mode",
                    return_value=("synthetic markdown", "pypdf_text"),
                ),
                patch("chem_pdf_extractor.extractor.extract_with_cloud_api", side_effect=fake_extract),
            ):
                thread = threading.Thread(
                    target=run_extraction_job,
                    args=(config, minimal_runtime(), state),
                    daemon=True,
                )
                thread.start()

                wait_until(lambda: state.snapshot()["pause_requested"] and output_path.exists())
                paused = state.snapshot()

                self.assertTrue(paused["running"])
                self.assertTrue(paused["pause_requested"])
                self.assertEqual(paused["pause_reason"], RESUMABLE_CLOUD_PAUSE_REASON)
                self.assertEqual(paused["current_retry_stage"], "cloud_llm_extraction")
                self.assertEqual(paused["success"], 1)
                self.assertEqual(paused["failed"], 0)
                self.assertEqual(paused["done"], 1)
                self.assertEqual(calls, ["001-success.pdf", "002-retry.pdf"])
                self.assertEqual(len(load_jsonl_rows(partial_path)), 1)
                self.assertFalse(error_stats_path.exists())

                state.request_resume()
                thread.join(timeout=8)
                self.assertFalse(thread.is_alive())

            finished = state.snapshot()
            self.assertFalse(finished["running"])
            self.assertFalse(finished["pause_requested"])
            self.assertEqual(finished["success"], 2)
            self.assertEqual(finished["failed"], 0)
            self.assertEqual(finished["done"], 2)
            self.assertEqual(calls, ["001-success.pdf", "002-retry.pdf", "002-retry.pdf"])
            self.assertEqual(len(load_jsonl_rows(partial_path)), 2)

            combined_status = json.dumps(finished, ensure_ascii=False)
            combined_logs = "\n".join(finished["logs"])
            diagnostic_logs = "\n".join(
                path.read_text(encoding="utf-8", errors="replace")
                for path in log_dir.glob("*.log")
            )
            leak_sources = "\n".join([combined_status, combined_logs, diagnostic_logs])
            for forbidden in [secret, private_text, prompt_text, response_text]:
                with self.subTest(forbidden=forbidden):
                    self.assertNotIn(forbidden, leak_sources)

    def test_transient_http_and_network_errors_are_classified_after_retries(self):
        for exc in [
            urllib.error.URLError("network unreachable"),
            urllib.error.HTTPError(
                "https://api.real-provider.test/v1/chat/completions",
                429,
                "too many requests",
                {},
                io.BytesIO(b"rate limited"),
            ),
            urllib.error.HTTPError(
                "https://api.real-provider.test/v1/chat/completions",
                503,
                "temporarily unavailable",
                {},
                io.BytesIO(b"temporary outage"),
            ),
        ]:
            with self.subTest(exc=type(exc).__name__, code=getattr(exc, "code", None)):
                with (
                    patch("chem_pdf_extractor.llm.CLOUD_RETRY_COUNT", 2),
                    patch("chem_pdf_extractor.llm.CLOUD_RETRY_BASE_DELAY_SECONDS", 0),
                    patch("chem_pdf_extractor.llm.CLOUD_RETRY_MAX_DELAY_SECONDS", 0),
                    patch("urllib.request.urlopen", side_effect=exc) as urlopen_mock,
                ):
                    with self.assertRaises(TransientCloudAPIError):
                        cloud_chat_completion(
                            "https://api.real-provider.test/v1",
                            "sk-test-secret-123456789",
                            "test-model",
                            [{"role": "user", "content": "safe"}],
                            1,
                        )
                    self.assertEqual(urlopen_mock.call_count, 2)

    def test_non_transient_config_and_auth_errors_fail_normally(self):
        missing_key_error = validate_cloud_start_config(
            {
                "llm_provider": "cloud",
                "cloud_base_url": "https://api.real-provider.test/v1",
                "cloud_model": "test-model",
                "cloud_api_key": "",
            }
        )

        self.assertIsNotNone(missing_key_error)
        self.assertIn("API Key", missing_key_error)
        self.assertFalse(is_transient_cloud_error(RuntimeError(missing_key_error)))

        with (
            patch("chem_pdf_extractor.llm.CLOUD_RETRY_COUNT", 2),
            patch("chem_pdf_extractor.llm.CLOUD_RETRY_BASE_DELAY_SECONDS", 0),
            patch("chem_pdf_extractor.llm.CLOUD_RETRY_MAX_DELAY_SECONDS", 0),
            patch(
                "urllib.request.urlopen",
                side_effect=urllib.error.HTTPError(
                    "https://api.real-provider.test/v1/chat/completions",
                    401,
                    "unauthorized",
                    {},
                    io.BytesIO(b'{"error":"bad key sk-test-secret-123456789"}'),
                ),
            ) as urlopen_mock,
        ):
            with self.assertRaises(RuntimeError) as ctx:
                cloud_chat_completion(
                    "https://api.real-provider.test/v1",
                    "sk-test-secret-123456789",
                    "test-model",
                    [{"role": "user", "content": "safe"}],
                    1,
                )

        self.assertNotIsInstance(ctx.exception, TransientCloudAPIError)
        self.assertEqual(urlopen_mock.call_count, 1)
        self.assertNotIn("sk-test-secret-123456789", str(ctx.exception))

    def test_existing_ui_layout_contract_remains_intact(self):
        template = (Path(__file__).resolve().parents[1] / "chem_pdf_extractor" / "templates" / "index.html").read_text(encoding="utf-8")

        self.assertIn("UI layout contract", template)
        self.assertIn("Only pre#logs may scroll internally", template)
        self.assertIn("docs/ui_layout_contract.md", template)
        self.assertIn('if (snapshot.pause_reason === "transient_cloud_failure") return "next_action_api_paused";', template)
        self.assertIn("next_action_api_paused", template)


if __name__ == "__main__":
    unittest.main()
