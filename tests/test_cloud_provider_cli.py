import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]


class CloudProviderCliTest(unittest.TestCase):
    def run_command(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["CHEM_PDF_EXTRACTOR_LOG_DIR"] = tmp
            env["PYTHONIOENCODING"] = "utf-8"
            return subprocess.run(
                [sys.executable, "-m", "chem_pdf_extractor", *args],
                cwd=REPO_ROOT,
                env=env,
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                check=False,
            )

    def test_cli_help_includes_local_and_cloud_guidance(self):
        result = self.run_command(["--help"])

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Local/private Ollama", result.stdout)
        self.assertIn("OpenAI-compatible cloud", result.stdout)
        self.assertIn("CHEM_PDF_EXTRACTOR_API_KEY", result.stdout)
        self.assertIn("CHEM_PDF_EXTRACTOR_BASE_URL", result.stdout)
        self.assertIn("CHEM_PDF_EXTRACTOR_MODEL", result.stdout)
        self.assertIn("Provider values", result.stdout)
        self.assertIn("cloud", result.stdout)
        self.assertIn("ollama", result.stdout)
        self.assertIn("first-pass data for human verification", result.stdout)

    def test_invalid_provider_error_lists_valid_values(self):
        result = self.run_command(["--llm-provider", "deepseek"])

        self.assertEqual(2, result.returncode)
        combined = result.stdout + result.stderr
        self.assertIn("invalid choice", combined)
        self.assertIn("cloud", combined)
        self.assertIn("ollama", combined)
        self.assertNotIn("API_KEY_VALUE_SHOULD_NOT_APPEAR", combined)

    def test_missing_cloud_api_key_error_is_safe_and_actionable(self):
        from chem_pdf_extractor import app

        args = app.parse_args(
            [
                "--cli",
                "--llm-provider",
                "cloud",
                "--cloud-base-url",
                "https://api.real-provider.test/v1",
                "--cloud-model",
                "test-model",
            ]
        )
        stderr = io.StringIO()
        with patch("chem_pdf_extractor.app.load_local_config", return_value={}):
            with patch.dict(
                os.environ,
                {
                    "CHEM_PDF_EXTRACTOR_API_KEY": "",
                    "CHEM_EXTRACTOR_CLOUD_API_KEY": "",
                    "CHEM_PDF_EXTRACTOR_BASE_URL": "",
                    "CHEM_PDF_EXTRACTOR_MODEL": "",
                },
                clear=False,
            ):
                with contextlib.redirect_stderr(stderr):
                    code = app.run_cli(args)

        output = stderr.getvalue()
        self.assertEqual(2, code)
        self.assertIn("CLI configuration error", output)
        self.assertIn("CHEM_PDF_EXTRACTOR_API_KEY", output)
        self.assertIn("--cloud-api-key", output)
        self.assertIn("--llm-provider ollama", output)

    def test_cli_validation_does_not_leak_api_key_value(self):
        from chem_pdf_extractor import app

        secret = "sk-test-SECRET-1234567890"
        args = app.parse_args(
            [
                "--cli",
                "--llm-provider",
                "cloud",
                "--cloud-api-key",
                secret,
                "--cloud-base-url",
                "https://api.real-provider.test/v1",
                "--cloud-model",
                "provider/model-name",
            ]
        )
        stderr = io.StringIO()
        with patch("chem_pdf_extractor.app.load_local_config", return_value={}):
            with contextlib.redirect_stderr(stderr):
                code = app.run_cli(args)

        output = stderr.getvalue()
        self.assertEqual(2, code)
        self.assertIn("CLI configuration error", output)
        self.assertIn("--cloud-model", output)
        self.assertNotIn(secret, output)

    def test_cloud_mode_accepts_legacy_model_alias_for_cloud_model(self):
        from chem_pdf_extractor import app
        from chem_pdf_extractor.config import validate_cloud_start_config

        args = app.parse_args(
            [
                "--cli",
                "--llm-provider",
                "cloud",
                "--cloud-api-key",
                "sk-test-safe-123456",
                "--cloud-base-url",
                "https://api.real-provider.test/v1",
                "--model",
                "provider/test-cloud-model",
            ]
        )
        with patch("chem_pdf_extractor.app.load_local_config", return_value={}):
            config = app.build_cli_config(args)

        self.assertEqual("provider/test-cloud-model", config["cloud_model"])
        self.assertEqual("provider/test-cloud-model", config["model"])
        self.assertIsNone(validate_cloud_start_config(config))


if __name__ == "__main__":
    unittest.main()
