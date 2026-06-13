import json
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch

from chem_pdf_extractor.config import RuntimeDeps
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
        self.url = f"http://127.0.0.1:{self.app.port}/api/cloud-test"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def post_cloud_test(self, payload, token="local-test-token"):
        headers = {"Content-Type": "application/json"}
        if token is not None:
            headers["X-Chem-PDF-Extractor-Token"] = token
        request = urllib.request.Request(
            self.url,
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


if __name__ == "__main__":
    unittest.main()
