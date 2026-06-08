import json
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from chem_pdf_extractor.llm import (
    build_openai_compatible_models_url,
    fetch_openai_compatible_models,
)


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class ModelDiscoveryTest(unittest.TestCase):
    def test_build_models_url_handles_base_url_without_trailing_slash(self):
        self.assertEqual(
            build_openai_compatible_models_url("https://api.example.com/v1"),
            "https://api.example.com/v1/models",
        )

    def test_build_models_url_handles_base_url_with_trailing_slash(self):
        self.assertEqual(
            build_openai_compatible_models_url("https://api.example.com/v1/"),
            "https://api.example.com/v1/models",
        )

    def test_fetch_models_parses_openai_compatible_response(self):
        requests = []

        def fake_urlopen(request, timeout=0):
            requests.append((request.full_url, request.get_header("Authorization"), timeout))
            return FakeResponse({"data": [{"id": "model-a"}, {"id": "model-b"}]})

        with patch("chem_pdf_extractor.llm.urllib.request.urlopen", fake_urlopen):
            models = fetch_openai_compatible_models("https://api.example.com/v1", "TEST_KEY", timeout=3)

        self.assertEqual(models, ["model-a", "model-b"])
        self.assertEqual(requests[0][0], "https://api.example.com/v1/models")
        self.assertEqual(requests[0][1], "Bearer TEST_KEY")
        self.assertEqual(requests[0][2], 3)

    def test_fetch_models_deduplicates_ids(self):
        def fake_urlopen(request, timeout=0):
            return FakeResponse({"data": [{"id": "model-a"}, {"id": "model-a"}, {"id": "model-b"}]})

        with patch("chem_pdf_extractor.llm.urllib.request.urlopen", fake_urlopen):
            models = fetch_openai_compatible_models("https://api.example.com/v1/", "TEST_KEY")

        self.assertEqual(models, ["model-a", "model-b"])

    def test_fetch_models_rejects_invalid_response(self):
        def fake_urlopen(request, timeout=0):
            return FakeResponse({"models": []})

        with patch("chem_pdf_extractor.llm.urllib.request.urlopen", fake_urlopen):
            with self.assertRaisesRegex(RuntimeError, "Failed to fetch models"):
                fetch_openai_compatible_models("https://api.example.com/v1", "TEST_KEY")

    def test_fetch_models_error_does_not_include_api_key(self):
        secret = "SECRET_TEST_KEY"

        def fake_urlopen(request, timeout=0):
            raise urllib.error.URLError(f"network failure {secret}")

        with patch("chem_pdf_extractor.llm.urllib.request.urlopen", fake_urlopen):
            with self.assertRaises(RuntimeError) as context:
                fetch_openai_compatible_models("https://api.example.com/v1", secret)

        self.assertNotIn(secret, str(context.exception))

    def test_config_example_is_provider_neutral(self):
        config_path = Path(__file__).resolve().parent.parent / "config.example.json"
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        raw_text = config_path.read_text(encoding="utf-8").lower()

        self.assertEqual(payload["llm_service_name"], "openai_compatible")
        self.assertEqual(payload["api_key"], "YOUR_API_KEY_HERE")
        self.assertEqual(payload["base_url"], "https://api.example.com/v1")
        self.assertEqual(payload["model"], "provider/model-name")
        self.assertFalse(payload["cloud_active"])
        for forbidden in ["silicon", "siliconflow", "deepseek", "openrouter"]:
            self.assertNotIn(forbidden, raw_text)


if __name__ == "__main__":
    unittest.main()
