import os
import re
import subprocess
import sys
import tempfile
import unittest
from importlib import resources
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class PackageDataTest(unittest.TestCase):
    def test_pyproject_declares_console_script(self):
        content = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")

        self.assertIn("[project.scripts]", content)
        self.assertRegex(
            content,
            re.compile(
                r'^chem-pdf-extractor\s*=\s*"chem_pdf_extractor\.entrypoint:run"$',
                re.MULTILINE,
            ),
        )

    def test_pyproject_declares_html_template_package_data(self):
        content = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")

        self.assertIn("[tool.setuptools.package-data]", content)
        self.assertRegex(
            content,
            re.compile(
                r'^chem_pdf_extractor\s*=\s*\["templates/index\.html"\]$',
                re.MULTILINE,
            ),
        )

    def test_template_file_resolves_from_package_resources(self):
        template = resources.files("chem_pdf_extractor").joinpath("templates", "index.html")

        content = template.read_text(encoding="utf-8")

        self.assertIn("<!doctype html>", content.lower())
        self.assertIn("Chem-PDF-Extractor", content)

    def test_server_import_and_template_load_succeeds(self):
        from chem_pdf_extractor.server import load_html_template

        content = load_html_template()

        self.assertIn("Chem-PDF-Extractor", content)
        self.assertIn("__DEFAULT_FIELDS_JSON__", content)

    def test_python_module_entrypoint_still_supports_help(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["CHEM_PDF_EXTRACTOR_LOG_DIR"] = tmp
            env["PYTHONIOENCODING"] = "utf-8"
            result = subprocess.run(
                [sys.executable, "-m", "chem_pdf_extractor", "--help"],
                cwd=REPO_ROOT,
                env=env,
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                check=False,
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("--cli", result.stdout)

    def test_ci_declares_lightweight_package_check(self):
        workflow = (REPO_ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")

        self.assertIn("Wheel package check", workflow)
        self.assertIn("python -m build", workflow)
        self.assertIn("python -m pip install --force-reinstall dist/*.whl", workflow)
        self.assertIn("chem-pdf-extractor --help", workflow)
        self.assertIn("python -m chem_pdf_extractor --help", workflow)

    def test_constraints_file_uses_broad_upper_bounds(self):
        content = (REPO_ROOT / "constraints.txt").read_text(encoding="utf-8")

        self.assertIn("Release verification constraints", content)
        self.assertIn("pypdf<", content)
        self.assertIn("pydantic<", content)
        self.assertIn("pandas<", content)
        self.assertNotIn("==", content)

    def test_windows_package_docs_explain_release_constraints(self):
        content = (REPO_ROOT / "docs" / "windows_package.md").read_text(encoding="utf-8")

        self.assertIn("Release dependency constraints", content)
        self.assertIn("requirements.txt` or `requirements-core.txt` directly", content)
        self.assertIn("python -m pip install -r requirements.txt -c constraints.txt", content)
        self.assertIn("broad upper bounds instead of exact pins", content)
        self.assertIn("Refresh it when testing support for a new major dependency version", content)


if __name__ == "__main__":
    unittest.main()
