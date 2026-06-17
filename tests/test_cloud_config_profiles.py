import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from chem_pdf_extractor.config import (
    apply_cloud_config_defaults,
    infer_cloud_profile_names,
    load_local_config,
    normalize_local_config,
    public_local_config,
    save_local_config,
)
from chem_pdf_extractor.server import run_cloud_api_test


class CloudConfigProfilesTest(unittest.TestCase):
    def test_profile_name_inference_known_hosts(self):
        cases = [
            ("https://token-plan-cn.xiaomimimo.com/v1", "xiaomi_mimo", "Xiaomi Mimo", "小米 Mimo"),
            ("https://api.deepseek.com", "deepseek", "DeepSeek", "DeepSeek"),
            ("https://api.openai.com/v1", "openai", "OpenAI", "OpenAI"),
        ]

        for url, service_name, display_en, display_zh in cases:
            with self.subTest(url=url):
                names = infer_cloud_profile_names(url)
                self.assertEqual(names["service_name"], service_name)
                self.assertEqual(names["display_name_en"], display_en)
                self.assertEqual(names["display_name_zh"], display_zh)

    def test_profile_name_inference_unknown_hosts(self):
        self.assertEqual(infer_cloud_profile_names("https://api.example.com/v1")["display_name_en"], "Example")
        self.assertEqual(infer_cloud_profile_names("https://openrouter.ai/api/v1")["display_name_en"], "OpenRouter")

    def test_save_profile_writes_profiles_and_flat_compatibility_mirrors(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("chem_pdf_extractor.config.PROJECT_ROOT", Path(tmp)):
                save_local_config(
                    {
                        "base_url": "https://token-plan-cn.xiaomimimo.com/v1",
                        "api_key": "tp-cloud-secret-final-fp",
                        "model": "provider/model-name",
                        "cloud_active": True,
                    }
                )
                private = load_local_config()
                raw = json.loads((Path(tmp) / "config.local.json").read_text(encoding="utf-8"))

        self.assertEqual(private["active_cloud_profile_id"], "xiaomi_mimo")
        self.assertEqual(private["cloud_service_name"], "xiaomi_mimo")
        self.assertEqual(private["cloud_api_key"], "tp-cloud-secret-final-fp")
        self.assertEqual(private["cloud_base_url"], "https://token-plan-cn.xiaomimimo.com/v1")
        self.assertEqual(private["cloud_model"], "provider/model-name")
        self.assertEqual(raw["api_key"], "tp-cloud-secret-final-fp")
        self.assertEqual(raw["base_url"], "https://token-plan-cn.xiaomimimo.com/v1")
        self.assertEqual(raw["model"], "provider/model-name")
        self.assertEqual(raw["active_cloud_profile_id"], "xiaomi_mimo")
        self.assertEqual(raw["cloud_profiles"][0]["service_name"], "xiaomi_mimo")

    def test_saving_existing_profile_with_blank_key_keeps_saved_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("chem_pdf_extractor.config.PROJECT_ROOT", Path(tmp)):
                save_local_config(
                    {
                        "base_url": "https://api.deepseek.com/v1",
                        "api_key": "deepseek-secret-key",
                        "model": "deepseek-chat",
                        "cloud_active": True,
                    }
                )
                profile_id = load_local_config()["active_cloud_profile_id"]
                save_local_config(
                    {
                        "active_cloud_profile_id": profile_id,
                        "base_url": "https://api.deepseek.com/v1",
                        "api_key": "",
                        "model": "deepseek-reasoner",
                        "cloud_active": True,
                    }
                )
                private = load_local_config()

        self.assertEqual(private["cloud_api_key"], "deepseek-secret-key")
        self.assertEqual(private["cloud_model"], "deepseek-reasoner")
        self.assertEqual(private["cloud_profiles"][0]["api_key"], "deepseek-secret-key")

    def test_explicit_empty_profile_id_creates_second_profile_for_new_base_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("chem_pdf_extractor.config.PROJECT_ROOT", Path(tmp)):
                save_local_config(
                    {
                        "base_url": "https://token-plan-cn.xiaomimimo.com/v1",
                        "api_key": "xiaomi-secret-key",
                        "model": "mimo/model",
                        "cloud_active": True,
                    }
                )
                save_local_config(
                    {
                        "active_cloud_profile_id": "",
                        "base_url": "https://api.deepseek.com/v1",
                        "api_key": "deepseek-secret-key",
                        "model": "deepseek-chat",
                        "cloud_active": True,
                    }
                )
                private = load_local_config()

        profiles = {profile["id"]: profile for profile in private["cloud_profiles"]}
        self.assertEqual(set(profiles), {"xiaomi_mimo", "deepseek"})
        self.assertEqual(private["active_cloud_profile_id"], "deepseek")
        self.assertEqual(profiles["xiaomi_mimo"]["api_key"], "xiaomi-secret-key")
        self.assertEqual(profiles["xiaomi_mimo"]["base_url"], "https://token-plan-cn.xiaomimimo.com/v1")
        self.assertEqual(profiles["xiaomi_mimo"]["model"], "mimo/model")
        self.assertEqual(profiles["deepseek"]["api_key"], "deepseek-secret-key")
        self.assertEqual(profiles["deepseek"]["base_url"], "https://api.deepseek.com/v1")

    def test_blank_key_does_not_fall_back_to_active_profile_when_base_url_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("chem_pdf_extractor.config.PROJECT_ROOT", Path(tmp)):
                save_local_config(
                    {
                        "base_url": "https://token-plan-cn.xiaomimimo.com/v1",
                        "api_key": "xiaomi-secret-key",
                        "model": "mimo/model",
                        "cloud_active": True,
                    }
                )
                save_local_config(
                    {
                        "active_cloud_profile_id": "",
                        "base_url": "https://api.deepseek.com/v1",
                        "api_key": "",
                        "model": "deepseek-chat",
                        "cloud_active": True,
                    }
                )
                private = load_local_config()

        profiles = {profile["id"]: profile for profile in private["cloud_profiles"]}
        self.assertEqual(profiles["xiaomi_mimo"]["api_key"], "xiaomi-secret-key")
        self.assertEqual(profiles["deepseek"]["api_key"], "")
        self.assertEqual(private["active_cloud_profile_id"], "deepseek")
        self.assertEqual(private["cloud_api_key"], "")

    def test_apply_defaults_does_not_use_active_profile_key_for_mismatched_base_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("chem_pdf_extractor.config.PROJECT_ROOT", Path(tmp)):
                save_local_config(
                    {
                        "base_url": "https://token-plan-cn.xiaomimimo.com/v1",
                        "api_key": "xiaomi-secret-key",
                        "model": "mimo/model",
                        "cloud_active": True,
                    }
                )
                config = {
                    "llm_provider": "cloud",
                    "active_cloud_profile_id": "xiaomi_mimo",
                    "cloud_base_url": "https://api.deepseek.com/v1/",
                    "cloud_model": "deepseek-chat",
                    "cloud_api_key": "",
                }
                apply_cloud_config_defaults(config)

        self.assertEqual(config["cloud_api_key"], "")

    def test_public_config_never_exposes_full_saved_profile_api_key(self):
        secret = "sk-profile-secret-123456789"
        with tempfile.TemporaryDirectory() as tmp:
            with patch("chem_pdf_extractor.config.PROJECT_ROOT", Path(tmp)):
                save_local_config(
                    {
                        "base_url": "https://api.openai.com/v1",
                        "api_key": secret,
                        "model": "gpt-test",
                        "cloud_active": True,
                    }
                )
                public = public_local_config()

        self.assertNotIn(secret, str(public))
        self.assertNotIn("api_key", public)
        self.assertNotIn("cloud_api_key", public)
        self.assertTrue(public["has_cloud_api_key"])
        self.assertTrue(public["cloud_profiles"][0]["has_api_key"])
        self.assertIn("...", public["cloud_profiles"][0]["cloud_api_key_prefix"])

    def test_old_flat_config_still_loads_as_active_profile(self):
        payload = normalize_local_config(
            {
                "llm_service_name": "legacy_service",
                "api_key": "legacy-secret",
                "base_url": "https://legacy.example.test/v1",
                "model": "legacy-model",
                "cloud_active": True,
            }
        )

        self.assertEqual(payload["cloud_service_name"], "legacy_service")
        self.assertEqual(payload["cloud_api_key"], "legacy-secret")
        self.assertEqual(payload["cloud_model"], "legacy-model")
        self.assertEqual(payload["active_cloud_profile_id"], "legacy_service")
        self.assertEqual(payload["cloud_profiles"][0]["service_name"], "legacy_service")

    def test_cloud_api_test_can_use_saved_profile_key_when_input_key_blank(self):
        calls = []

        def fake_chat(base_url, api_key, model, timeout=0):
            calls.append(("chat", base_url, api_key, model, timeout))

        def fake_models(base_url, api_key, timeout=0):
            calls.append(("models", base_url, api_key, timeout))
            return ["deepseek-chat"]

        with tempfile.TemporaryDirectory() as tmp:
            with patch("chem_pdf_extractor.config.PROJECT_ROOT", Path(tmp)):
                save_local_config(
                    {
                        "base_url": "https://api.deepseek.com/v1",
                        "api_key": "saved-deepseek-key",
                        "model": "deepseek-chat",
                        "cloud_active": True,
                    }
                )
                profile_id = load_local_config()["active_cloud_profile_id"]
                with patch("chem_pdf_extractor.server.test_openai_compatible_chat", fake_chat), patch(
                    "chem_pdf_extractor.server.fetch_openai_compatible_models", fake_models
                ):
                    result = run_cloud_api_test(
                        {
                            "base_url": "https://api.deepseek.com/v1",
                            "api_key": "",
                            "model": "deepseek-chat",
                            "active_cloud_profile_id": profile_id,
                        }
                    )

        self.assertEqual(result["status"], "success")
        self.assertEqual(calls[0][2], "saved-deepseek-key")
        self.assertEqual(calls[1][2], "saved-deepseek-key")

    def test_cloud_api_test_does_not_use_saved_profile_key_for_mismatched_base_url(self):
        calls = []

        def fake_chat(base_url, api_key, model, timeout=0):
            calls.append(("chat", base_url, api_key, model, timeout))

        with tempfile.TemporaryDirectory() as tmp:
            with patch("chem_pdf_extractor.config.PROJECT_ROOT", Path(tmp)):
                save_local_config(
                    {
                        "base_url": "https://token-plan-cn.xiaomimimo.com/v1",
                        "api_key": "xiaomi-secret-key",
                        "model": "mimo/model",
                        "cloud_active": True,
                    }
                )
                with patch("chem_pdf_extractor.server.test_openai_compatible_chat", fake_chat):
                    result = run_cloud_api_test(
                        {
                            "base_url": "https://api.deepseek.com/v1",
                            "api_key": "",
                            "model": "deepseek-chat",
                            "active_cloud_profile_id": "xiaomi_mimo",
                        }
                    )

        self.assertEqual(result["status"], "failed")
        self.assertIn("api key", str(result["error"]).lower())
        self.assertEqual(calls, [])
        self.assertNotIn("xiaomi-secret-key", str(result))


if __name__ == "__main__":
    unittest.main()
