import re
import unittest
from pathlib import Path
from urllib.parse import unquote


REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class DocsLinksTest(unittest.TestCase):
    def test_readme_links_key_docs(self):
        content = read(README)

        for target in [
            "docs/configuration.md",
            "docs/use_case_catalysis_literature_extraction.md",
            "docs/evaluation.md",
            "examples/field_templates/README.md",
            "docs/ui_layout_contract.md",
            "docs/screenshot_guide.md",
            "docs/windows_package.md",
            "SECURITY.md",
            "ROADMAP.md",
        ]:
            with self.subTest(target=target):
                self.assertIn(target, content)
                self.assertTrue((REPO_ROOT / target).exists(), target)

    def test_readme_relative_links_and_images_exist(self):
        content = read(README)
        pattern = re.compile(r"!?\[[^\]]+\]\(([^)]+)\)")

        for raw_target in pattern.findall(content):
            target = raw_target.strip()
            if target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            target = target.split("#", 1)[0].split("?", 1)[0].strip()
            if not target:
                continue
            target_path = REPO_ROOT / unquote(target)
            with self.subTest(target=raw_target):
                self.assertTrue(target_path.exists(), raw_target)

    def test_readme_sets_honest_first_impression(self):
        content = read(README)
        lower = content.lower()

        for phrase in [
            "local-first",
            "first-pass",
            "human review",
            "workflow overview",
            "supported workflows",
            "web ui workflow",
            "cli workflow",
            "local ollama",
            "openai-compatible cloud",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, lower)

        for overclaim in [
            "production-grade scientific accuracy",
            "fully automated correctness",
            "widely used",
            "100% extraction accuracy",
        ]:
            with self.subTest(overclaim=overclaim):
                self.assertNotIn(overclaim, lower)

    def test_screenshot_guide_exists_and_sets_safety_rules(self):
        path = REPO_ROOT / "docs" / "screenshot_guide.md"
        content = read(path)

        for phrase in [
            "docs/screenshots/web-ui-zh+en.png",
            "docs/screenshots/excel-output-example.svg",
            "synthetic or public-safe",
            "Do not show private PDFs",
            "Do not show API keys",
            "Do not show private local paths",
            "Do not add fake screenshots",
            "Screenshots are illustrative only",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, content)


if __name__ == "__main__":
    unittest.main()
