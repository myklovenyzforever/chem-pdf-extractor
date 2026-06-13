import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from chem_pdf_extractor.config import load_local_config, public_local_config, save_local_config


class PublicConfigSecurityTest(unittest.TestCase):
    def test_public_local_config_does_not_return_raw_api_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("chem_pdf_extractor.config.PROJECT_ROOT", Path(tmp)):
                save_local_config(
                    {
                        "api_key": "sk-testSECRET123456",
                        "base_url": "https://api.provider.test/v1",
                        "model": "provider/model",
                        "cloud_active": True,
                    }
                )

                public = public_local_config()
                private = load_local_config()

        self.assertEqual(private["cloud_api_key"], "sk-testSECRET123456")
        self.assertNotIn("cloud_api_key", public)
        self.assertNotIn("api_key", public)
        self.assertTrue(public["has_cloud_api_key"])
        self.assertIn("...", public["cloud_api_key_prefix"])
        self.assertNotIn("sk-testSECRET123456", str(public))


if __name__ == "__main__":
    unittest.main()
