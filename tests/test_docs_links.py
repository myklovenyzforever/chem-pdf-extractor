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
            "docs/project_status_and_roadmap.md",
            "docs/screenshot_guide.md",
            "docs/release_and_feedback.md",
            "docs/windows_package.md",
            "CONTRIBUTING.md",
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

    def test_readme_aligns_v040_defaults(self):
        content = read(README)
        lower = content.lower()

        for phrase in [
            "mineru` is the v0.4.0 web ui/default mode",
            "`pymupdf4llm` is a lighter/balanced fallback",
            "`pypdf_text` is the smallest compatibility fallback",
            "default extraction text budget is `max_chars = 0`",
            "no truncation can be slower, costlier for cloud usage",
            "`--pdf-mode auto` is a heuristic mode",
            "not a guarantee of accurate layout recovery",
            "saved keys remain in local `config.local.json`",
            "not filled back into the browser ui",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, lower)

        for stale in [
            "pymupdf4llm` for the recommended default",
            "`pymupdf4llm`: recommended default",
            "default extraction text budget is 80k",
            "80k characters",
            "mineru is optional and is not installed by default",
        ]:
            with self.subTest(stale=stale):
                self.assertNotIn(stale, lower)

    def test_agent_and_contributor_guides_exist_with_safety_rules(self):
        agents = REPO_ROOT / "AGENTS.md"
        contributing = REPO_ROOT / "CONTRIBUTING.md"
        self.assertTrue(agents.exists())
        self.assertTrue(contributing.exists())

        agents_content = read(agents)
        contributing_content = read(contributing)
        agents_lower = agents_content.lower()
        contributing_lower = contributing_content.lower()

        for phrase in [
            "python -m unittest discover -s tests -v",
            "python -m chem_pdf_extractor --help",
            "git diff --check",
            "release_artifacts/",
            "config.local.json",
            "cloud api keys local-only",
            "local-loopback safety model",
        ]:
            with self.subTest(agent_phrase=phrase):
                self.assertIn(phrase, agents_lower)

        for phrase in [
            "synthetic or public-safe",
            "api keys",
            "private pdfs",
            "small and focused",
            "python -m unittest discover -s tests -v",
            "python -m chem_pdf_extractor --help",
            "git diff --check",
            "release_artifacts/",
            "security.md",
        ]:
            with self.subTest(contributing_phrase=phrase):
                self.assertIn(phrase, contributing_lower)

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

    def test_release_feedback_doc_exists_and_sets_safe_path(self):
        path = REPO_ROOT / "docs" / "release_and_feedback.md"
        content = read(path)
        lower = content.lower()
        readme_content = read(README)

        self.assertIn("docs/release_and_feedback.md", readme_content)

        for phrase in [
            "maintainer release checklist",
            "working tree is clean",
            "python -m unittest discover -s tests -v",
            "python -m chem_pdf_extractor --help",
            "no generated artifacts are staged",
            "user feedback paths",
            "extraction quality issues",
            "incorrect or missing fields",
            "field template suggestions",
            "pdf mode or parser problems",
            "local ollama setup issues",
            "optional cloud provider configuration issues",
            "packaging or windows install issues",
            "documentation gaps",
            "do not upload private pdfs",
            "do not paste api keys",
            "do not paste copyrighted paper text",
            "do not paste confidential user",
            "redact private local paths",
            "avoid pasting full cloud responses",
            "bug",
            "docs",
            "extraction quality",
            "template suggestion",
            "packaging/install",
            "security/privacy concern",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, lower)

        forbidden_terms = [
            "cod" + "ex for " + "oss",
            "open" + "ai " + "cre" + "dits",
            "open" + "ai " + "sponsor" + "ship",
            "open" + "ai " + "fund" + "ing",
            "sponsor" + "ship",
            "fund" + "ing",
            "accept" + "ance",
            "cre" + "dits",
        ]
        for forbidden in forbidden_terms:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, lower)

    def test_project_status_doc_exists_and_sets_maintainer_roadmap(self):
        path = REPO_ROOT / "docs" / "project_status_and_roadmap.md"
        content = read(path)
        lower = content.lower()
        readme_content = read(README)

        self.assertIn("docs/project_status_and_roadmap.md", readme_content)

        for phrase in [
            "local-first tool for chemistry and chemical engineering pdf extraction",
            "first-pass literature review",
            "not automated scientific correctness",
            "checked by a human",
            "tests covering core extraction flow",
            "synthetic/public-safe benchmark examples",
            "release checklist",
            "single maintainer",
            "limited review bandwidth",
            "small, focused",
            "minimal synthetic or public-safe reproductions",
            "privacy-conscious",
            "issue #7",
            "rag-like ideas remain future exploration",
            "rag is not current functionality",
            "retrieval-assisted chunk selection",
            "local-first indexing",
            "evidence linking",
            "table-aware and section-aware retrieval",
            "benchmark-driven evaluation",
            "broader adoption evidence should be added only when it exists",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, lower)

        overclaims = [
            "wide" + "ly used",
            "large user " + "base",
            "many production " + "deployments",
            "institutional " + "use",
            "test" + "imonials",
            "production-grade scientific " + "accuracy",
            "fully automated " + "correctness",
            "guaranteed " + "accuracy",
        ]
        for overclaim in overclaims:
            with self.subTest(overclaim=overclaim):
                self.assertNotIn(overclaim, lower)

        forbidden_terms = [
            "cod" + "ex for " + "oss",
            "open" + "ai " + "application",
            "open" + "ai " + "cre" + "dits",
            "open" + "ai " + "sponsor" + "ship",
            "open" + "ai " + "fund" + "ing",
            "open" + "ai " + "support",
            "sponsor" + "ship",
            "fund" + "ing",
            "accept" + "ance",
            "cre" + "dits",
        ]
        for forbidden in forbidden_terms:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, lower)


if __name__ == "__main__":
    unittest.main()
