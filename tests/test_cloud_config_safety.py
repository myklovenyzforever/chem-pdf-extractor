import unittest
from pathlib import Path
from unittest.mock import patch

from chem_pdf_extractor.config import apply_cloud_config_defaults, validate_cloud_start_config


ROOT = Path(__file__).resolve().parent.parent


class CloudConfigSafetyTest(unittest.TestCase):
    def test_cloud_start_validation_rejects_missing_api_key(self):
        error = validate_cloud_start_config(
            {
                "llm_provider": "cloud",
                "cloud_base_url": "https://api.real-provider.test/v1",
                "cloud_model": "test-model",
                "cloud_api_key": "",
            }
        )

        self.assertIsNotNone(error)
        self.assertIn("API Key", error)

    def test_cloud_start_validation_rejects_placeholder_base_url(self):
        secret = "SECRET_TEST_KEY"
        error = validate_cloud_start_config(
            {
                "llm_provider": "cloud",
                "cloud_api_key": secret,
                "cloud_base_url": "https://api.example.com/v1",
                "cloud_model": "test-model",
            }
        )

        self.assertIsNotNone(error)
        self.assertIn("Base URL", error)
        self.assertNotIn(secret, error)

    def test_cloud_start_validation_rejects_placeholder_model(self):
        secret = "SECRET_TEST_KEY"
        error = validate_cloud_start_config(
            {
                "llm_provider": "cloud",
                "cloud_api_key": secret,
                "cloud_base_url": "https://api.real-provider.test/v1",
                "cloud_model": "provider/model-name",
            }
        )

        self.assertIsNotNone(error)
        self.assertIn("模型", error)
        self.assertNotIn(secret, error)

    def test_cloud_start_validation_accepts_complete_cloud_config(self):
        error = validate_cloud_start_config(
            {
                "llm_provider": "cloud",
                "cloud_api_key": "SECRET_TEST_KEY",
                "cloud_base_url": "https://api.real-provider.test/v1",
                "cloud_model": "test-model",
            }
        )

        self.assertIsNone(error)

    def test_cloud_start_validation_ignores_ollama_provider(self):
        error = validate_cloud_start_config(
            {
                "llm_provider": "ollama",
                "cloud_api_key": "",
                "cloud_base_url": "https://api.example.com/v1",
                "cloud_model": "provider/model-name",
            }
        )

        self.assertIsNone(error)

    def test_cloud_start_validation_supports_api_key_and_model_aliases(self):
        error = validate_cloud_start_config(
            {
                "llm_provider": "cloud",
                "api_key": "SECRET_TEST_KEY",
                "base_url": "https://api.real-provider.test/v1",
                "model": "test-model",
            }
        )

        self.assertIsNone(error)

    def test_cloud_validation_error_does_not_leak_api_key_for_all_failures(self):
        secret = "SECRET_TEST_KEY"
        failing_configs = [
            {
                "llm_provider": "cloud",
                "cloud_api_key": secret,
                "cloud_base_url": "https://api.example.com/v1",
                "cloud_model": "test-model",
            },
            {
                "llm_provider": "cloud",
                "cloud_api_key": secret,
                "cloud_base_url": "https://api.real-provider.test/v1",
                "cloud_model": "provider/model-name",
            },
            {
                "llm_provider": "cloud",
                "cloud_api_key": secret,
                "cloud_base_url": "https://api.real-provider.test/v1",
                "cloud_model": "",
            },
        ]

        for config in failing_configs:
            with self.subTest(config=config):
                error = validate_cloud_start_config(config)
                self.assertIsNotNone(error)
                self.assertNotIn(secret, error)

    def test_cloud_active_defaults_false_without_local_config(self):
        config = {"llm_provider": "cloud"}

        with patch("chem_pdf_extractor.config.load_local_config", return_value={}):
            apply_cloud_config_defaults(config)

        self.assertFalse(config["cloud_active"])

    def test_server_prefers_cloud_models_endpoint_for_cloud_discovery(self):
        template = (ROOT / "chem_pdf_extractor" / "templates" / "index.html").read_text(encoding="utf-8")
        server = (ROOT / "chem_pdf_extractor" / "server.py").read_text(encoding="utf-8")

        self.assertIn('apiFetch("/api/cloud-models"', template)
        self.assertNotIn('apiFetch("/api/models", {', template)
        self.assertIn("GET /api/models is for local Ollama model discovery.", server)
        self.assertIn("POST /api/cloud-models is the preferred OpenAI-compatible model discovery endpoint.", server)
        self.assertIn("POST /api/models is kept as a compatibility alias", server)
        self.assertIn('parsed.path in {"/api/cloud-models", "/api/models"}', server)
        self.assertIn('parsed.path == "/api/models"', server)

    def test_server_validates_cloud_config_before_starting_thread(self):
        server = (ROOT / "chem_pdf_extractor" / "server.py").read_text(encoding="utf-8")

        self.assertIn("validate_cloud_start_config(config)", server)
        self.assertLess(server.index("validate_cloud_start_config(config)"), server.index("thread = threading.Thread"))

    def test_release_package_readme_removed(self):
        self.assertFalse((ROOT / "release_package" / "README.md").exists())
        self.assertTrue((ROOT / "docs" / "windows_package.md").exists())

    def test_legacy_cloud_model_helpers_removed_if_unused(self):
        llm_source = (ROOT / "chem_pdf_extractor" / "llm.py").read_text(encoding="utf-8")

        self.assertNotIn("def fetch_cloud_models_once", llm_source)
        self.assertNotIn("def get_cloud_models", llm_source)
        self.assertNotIn("def parse_model_ids", llm_source)


if __name__ == "__main__":
    unittest.main()
