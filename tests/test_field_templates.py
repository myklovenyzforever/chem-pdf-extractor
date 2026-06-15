import json
import re
import unittest
from pathlib import Path


class FieldTemplatesTest(unittest.TestCase):
    TEMPLATE_DIR = Path("examples/field_templates")
    TEMPLATE_FILES = [
        "catalysis_reaction.json",
        "materials_synthesis.json",
        "environmental_treatment.json",
        "electrochemistry.json",
    ]
    VALID_REQUIREMENTS = {"required", "recommended", "optional"}
    LABEL_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
    FORBIDDEN_JSON_TEXT = [
        "sk-",
        "api_key",
        "API_KEY",
        "C:\\",
        "D:\\",
        "Users\\",
        "config.local.json",
        "private.pdf",
        "unpublished manuscript",
        "confidential result",
    ]

    def test_template_directory_and_files_exist(self):
        self.assertTrue(self.TEMPLATE_DIR.is_dir())
        self.assertTrue((self.TEMPLATE_DIR / "README.md").is_file())
        for filename in self.TEMPLATE_FILES:
            self.assertTrue((self.TEMPLATE_DIR / filename).is_file())

    def test_templates_are_valid_field_lists(self):
        for filename in self.TEMPLATE_FILES:
            with self.subTest(filename=filename):
                path = self.TEMPLATE_DIR / filename
                text = path.read_text(encoding="utf-8")
                for token in self.FORBIDDEN_JSON_TEXT:
                    self.assertNotIn(token, text)

                fields = json.loads(text)
                self.assertIsInstance(fields, list)
                self.assertGreaterEqual(len(fields), 8)
                self.assertTrue(
                    any(field.get("requirement") == "required" for field in fields)
                )

                for field in fields:
                    self.assertIn("label", field)
                    self.assertIn("requirement", field)
                    self.assertIn("description", field)

                    label = field["label"]
                    requirement = field["requirement"]
                    description = field["description"]

                    self.assertIsInstance(label, str)
                    self.assertRegex(label, self.LABEL_RE)
                    self.assertIn(requirement, self.VALID_REQUIREMENTS)
                    self.assertIsInstance(description, str)
                    self.assertTrue(description.strip())

    def test_readme_mentions_every_template_and_workflow(self):
        readme = (self.TEMPLATE_DIR / "README.md").read_text(encoding="utf-8")
        for filename in self.TEMPLATE_FILES:
            with self.subTest(filename=filename):
                self.assertIn(filename, readme)

        required_phrases = [
            "Field templates are reusable",
            "Choosing A Template",
            "Using Templates In The Web UI",
            "Using Templates With CLI Or Config Files",
            "Requirement Levels",
            "required",
            "recommended",
            "optional",
            "Manual verification",
        ]
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, readme)

    def test_readme_documents_template_safety_and_issue_11_workflow(self):
        readme = (self.TEMPLATE_DIR / "README.md").read_text(encoding="utf-8")
        safety_phrases = [
            "synthetic or public-safe examples only",
            "Do not upload copyrighted papers",
            "private PDFs",
            "API keys",
            "private local paths",
            "config.local.json",
            "issue #11",
            "field-template suggestion workflow",
        ]
        for phrase in safety_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, readme)

    def test_readme_documents_each_template_review_details(self):
        readme = (self.TEMPLATE_DIR / "README.md").read_text(encoding="utf-8")
        expected_detail_labels = [
            "Domain:",
            "Suitable literature type:",
            "Key required fields:",
            "Recommended fields:",
            "Optional fields:",
            "Common extraction mistakes:",
            "Recommended PDF mode:",
            "Manual verification advice:",
        ]
        for filename in self.TEMPLATE_FILES:
            section_start = readme.index(f"### `{filename}`")
            next_section = readme.find("\n### `", section_start + 1)
            section = readme[section_start:] if next_section == -1 else readme[section_start:next_section]
            for label in expected_detail_labels:
                with self.subTest(filename=filename, label=label):
                    self.assertIn(label, section)


if __name__ == "__main__":
    unittest.main()
