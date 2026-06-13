import unittest

from chem_pdf_extractor.config import validate_cloud_base_url_security
from chem_pdf_extractor.llm import fetch_openai_compatible_models


class CloudBaseUrlSecurityTest(unittest.TestCase):
    def test_base_url_security_allows_safe_urls(self):
        for url in [
            "https://api.openai.com/v1",
            "https://example.com/v1",
            "http://127.0.0.1:8000/v1",
            "http://localhost:8000/v1",
            "http://[::1]:8000/v1",
        ]:
            with self.subTest(url=url):
                self.assertIsNone(validate_cloud_base_url_security(url))

    def test_base_url_security_rejects_unsafe_urls(self):
        rejected = {
            "http://example.com/v1": "HTTPS",
            "ftp://example.com/v1": "scheme",
            "https://user:pass@example.com/v1": "username/password",
            "https://example.com/v1?x=1": "query",
            "https://example.com/v1#frag": "fragment",
            "https://api.example.com/v1": "real",
        }
        for url, expected in rejected.items():
            with self.subTest(url=url):
                error = validate_cloud_base_url_security(url)
                self.assertIsNotNone(error)
                self.assertIn(expected, error)

    def test_model_discovery_rejects_unsafe_http_before_network(self):
        with self.assertRaisesRegex(RuntimeError, "HTTPS"):
            fetch_openai_compatible_models("http://example.com/v1", "sk-testSECRET123456")


if __name__ == "__main__":
    unittest.main()
