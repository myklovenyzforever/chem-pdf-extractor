import unittest

from chem_pdf_extractor.server import (
    allowed_ui_origins,
    validate_local_api_request,
)


class LocalApiSecurityTest(unittest.TestCase):
    def test_allowed_ui_origins_are_local_only(self):
        self.assertEqual(
            allowed_ui_origins(8766),
            {"http://127.0.0.1:8766", "http://localhost:8766"},
        )

    def test_local_api_requires_token_and_loopback(self):
        kwargs = {
            "expected_token": "token",
            "client_address": ("127.0.0.1", 12345),
            "origin": "http://127.0.0.1:8766",
            "referer": "http://127.0.0.1:8766/",
            "port": 8766,
        }
        self.assertTrue(validate_local_api_request(token="token", **kwargs))
        self.assertFalse(validate_local_api_request(token="wrong", **kwargs))
        self.assertFalse(validate_local_api_request(token="token", **{**kwargs, "client_address": ("192.168.1.2", 1)}))
        self.assertFalse(validate_local_api_request(token="token", **{**kwargs, "origin": "https://evil.test"}))
        self.assertFalse(validate_local_api_request(token="token", **{**kwargs, "referer": "https://evil.test/page"}))

    def test_missing_origin_referer_allowed_with_valid_token_for_compatibility(self):
        self.assertTrue(
            validate_local_api_request(
                token="token",
                expected_token="token",
                client_address=("::1", 12345),
                origin=None,
                referer=None,
                port=8766,
            )
        )


if __name__ == "__main__":
    unittest.main()
