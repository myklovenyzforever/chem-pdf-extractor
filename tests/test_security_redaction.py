import unittest

from chem_pdf_extractor.security import redact_sensitive_obj, redact_sensitive_text


class SecurityRedactionTest(unittest.TestCase):
    def test_redacts_common_secret_patterns(self):
        secret = "sk-testSECRET123456"
        text = (
            f"Authorization: Bearer {secret}\n"
            f"api_key={secret}\n"
            f'"token": "{secret}"\n'
            f"--cloud-api-key {secret}\n"
            f"--api-key={secret}\n"
            f"tp-testSECRET123456"
        )

        redacted = redact_sensitive_text(text)

        self.assertNotIn(secret, redacted)
        self.assertIn("<redacted>", redacted)
        self.assertIn("\n", redacted)

    def test_redacts_nested_objects(self):
        obj = {
            "api_key": "sk-testSECRET123456",
            "nested": {"message": "Bearer sk-testSECRET123456"},
        }

        redacted = redact_sensitive_obj(obj)

        self.assertEqual(redacted["api_key"], "<redacted>")
        self.assertNotIn("sk-testSECRET123456", redacted["nested"]["message"])


if __name__ == "__main__":
    unittest.main()
