import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class ReleaseMetadataTest(unittest.TestCase):
    def test_pyproject_uses_v021_beta_metadata(self):
        content = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")

        self.assertIn('version = "0.2.1"', content)
        self.assertIn("Development Status :: 4 - Beta", content)

    def test_changelog_contains_v020_and_v021_release_notes(self):
        content = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

        self.assertIn("## v0.2.1", content)
        self.assertIn("## v0.2.0", content)
        self.assertIn("Windows first-run launcher", content)
        self.assertIn("optional MinerU", content)
        self.assertTrue(
            "UTF-8 console setup" in content or "mojibake" in content,
            "Changelog should mention the launcher UTF-8/mojibake patch.",
        )

    def test_readme_screenshot_wording_is_release_tolerant(self):
        content = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        chinese_release_tolerant_text = "\u622a\u56fe\u53ef\u80fd\u968f\u7248\u672c\u7565\u6709\u53d8\u5316"
        chinese_synthetic_data_text = "\u8f93\u51fa\u9884\u89c8\u4ec5\u4f7f\u7528\u5408\u6210\u6570\u636e"

        self.assertIn("Screenshots may vary slightly between releases.", content)
        self.assertIn(chinese_release_tolerant_text, content)
        self.assertIn("synthetic data only", content)
        self.assertIn(chinese_synthetic_data_text, content)


if __name__ == "__main__":
    unittest.main()
