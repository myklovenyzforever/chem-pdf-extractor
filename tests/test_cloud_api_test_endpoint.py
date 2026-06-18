import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

from chem_pdf_extractor.config import RuntimeDeps, save_local_config
from chem_pdf_extractor import server as server_module


class CloudApiTestEndpointTest(unittest.TestCase):
    def setUp(self):
        runtime = RuntimeDeps(
            pd=None,
            PdfReader=None,
            ChatPromptTemplate=None,
            ChatOllama=None,
            Field=None,
            create_model=None,
        )
        self.app = server_module.ChemExtractorApp(runtime)
        self.app.ui_token = "local-test-token"
        self.server = server_module.ThreadingHTTPServer(("127.0.0.1", 0), server_module.RequestHandler)
        self.app.port = int(self.server.server_address[1])
        self.app.server = self.server
        server_module.RequestHandler.app = self.app
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.app.port}"
        self.url = f"{self.base_url}/api/cloud-test"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def post_api(self, path, payload, token="local-test-token"):
        headers = {"Content-Type": "application/json"}
        if token is not None:
            headers["X-Chem-PDF-Extractor-Token"] = token
        request = urllib.request.Request(
            self.base_url + path,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                body = response.read().decode("utf-8")
                return response.status, body, json.loads(body)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8")
            return exc.code, body, json.loads(body)

    def post_cloud_test(self, payload, token="local-test-token"):
        return self.post_api("/api/cloud-test", payload, token=token)

    def test_cloud_test_endpoint_requires_local_ui_token(self):
        status, _body, payload = self.post_cloud_test({}, token=None)

        self.assertEqual(status, 403)
        self.assertFalse(payload["ok"])

    def test_cloud_test_rejects_unsafe_base_url_without_network(self):
        with patch.object(server_module, "test_openai_compatible_chat") as chat_mock:
            status, body, payload = self.post_cloud_test(
                {
                    "base_url": "http://example.com/v1",
                    "api_key": "REAL_SECRET_KEY_123",
                    "model": "real-model",
                }
            )

        self.assertEqual(status, 200)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["status"], "failed")
        self.assertIn("HTTPS", body)
        chat_mock.assert_not_called()

    def test_cloud_test_rejects_placeholder_api_key(self):
        status, body, payload = self.post_cloud_test(
            {
                "base_url": "https://api.real-provider.test/v1",
                "api_key": "YOUR_API_KEY_HERE",
                "model": "real-model",
            }
        )

        self.assertEqual(status, 200)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["status"], "failed")
        self.assertIn("real LLM API key", body)

    def test_cloud_test_does_not_persist_config(self):
        with (
            patch.object(server_module, "test_openai_compatible_chat", return_value={"ok": True}),
            patch.object(server_module, "fetch_openai_compatible_models", return_value=["real-model"]),
            patch.object(server_module, "save_local_config") as save_mock,
        ):
            _status, _body, payload = self.post_cloud_test(
                {
                    "base_url": "https://api.real-provider.test/v1",
                    "api_key": "REAL_SECRET_KEY_123",
                    "model": "real-model",
                }
            )

        self.assertTrue(payload["ok"])
        self.assertEqual(payload["status"], "success")
        save_mock.assert_not_called()

    def test_cloud_test_returns_sanitized_error_without_full_api_key(self):
        secret = "REAL_SECRET_KEY_123"

        with patch.object(
            server_module,
            "test_openai_compatible_chat",
            side_effect=RuntimeError(f"network failure {secret}"),
        ):
            _status, body, payload = self.post_cloud_test(
                {
                    "base_url": "https://api.real-provider.test/v1",
                    "api_key": secret,
                    "model": "real-model",
                }
            )

        self.assertFalse(payload["ok"])
        self.assertEqual(payload["status"], "failed")
        self.assertNotIn(secret, body)
        self.assertIn("<redacted>", body)

    def test_cloud_test_reports_partial_when_model_list_is_unavailable(self):
        secret = "REAL_SECRET_KEY_123"

        with (
            patch.object(server_module, "test_openai_compatible_chat", return_value={"ok": True}),
            patch.object(
                server_module,
                "fetch_openai_compatible_models",
                side_effect=RuntimeError(f"model list unavailable {secret}"),
            ),
        ):
            _status, body, payload = self.post_cloud_test(
                {
                    "base_url": "https://api.real-provider.test/v1",
                    "api_key": secret,
                    "model": "real-model",
                }
            )

        self.assertTrue(payload["ok"])
        self.assertEqual(payload["status"], "partial")
        self.assertNotIn(secret, body)

    def test_cloud_profile_delete_endpoint_clears_active_without_returning_full_key(self):
        xiaomi_secret = "XIAOMI_SECRET_KEY_123"
        deepseek_secret = "DEEPSEEK_SECRET_KEY_456"
        with tempfile.TemporaryDirectory() as tmp:
            with patch("chem_pdf_extractor.config.PROJECT_ROOT", Path(tmp)):
                save_local_config(
                    {
                        "base_url": "https://token-plan-cn.xiaomimimo.com/v1",
                        "api_key": xiaomi_secret,
                        "model": "mimo/model",
                        "cloud_active": True,
                    }
                )
                save_local_config(
                    {
                        "active_cloud_profile_id": "",
                        "base_url": "https://api.deepseek.com/v1",
                        "api_key": deepseek_secret,
                        "model": "deepseek-chat",
                        "cloud_active": True,
                    }
                )
                status, body, payload = self.post_api(
                    "/api/cloud-profiles/delete",
                    {"profile_id": "deepseek"},
                )

        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["config"]["active_cloud_profile_id"], "")
        self.assertFalse(payload["config"]["has_cloud_api_key"])
        self.assertNotIn(xiaomi_secret, body)
        self.assertNotIn(deepseek_secret, body)
        self.assertNotIn("api_key", payload["config"])
        self.assertNotIn("cloud_api_key", payload["config"])

    def test_cloud_profile_delete_endpoint_missing_profile_is_safe(self):
        secret = "REQUEST_SECRET_KEY_123"
        with tempfile.TemporaryDirectory() as tmp:
            with patch("chem_pdf_extractor.config.PROJECT_ROOT", Path(tmp)):
                status, body, payload = self.post_api(
                    "/api/cloud-profiles/delete",
                    {"profile_id": "missing", "api_key": secret},
                )

        self.assertEqual(status, 404)
        self.assertFalse(payload["ok"])
        self.assertIn("not found", payload["error"].lower())
        self.assertNotIn(secret, body)


if __name__ == "__main__":
    unittest.main()
