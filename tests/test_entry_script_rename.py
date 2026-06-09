import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
OLD_SCRIPT_NAME = "ShuJuTiQuJiaoBen.py"
NEW_SCRIPT_NAME = "run_chem_pdf_extractor.py"


class EntryScriptRenameTest(unittest.TestCase):
    def run_help(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["CHEM_PDF_EXTRACTOR_LOG_DIR"] = tmp
            env["PYTHONIOENCODING"] = "utf-8"
            return subprocess.run(
                command,
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

    def test_new_entry_script_exists(self):
        self.assertTrue((REPO_ROOT / NEW_SCRIPT_NAME).exists())
        self.assertFalse((REPO_ROOT / OLD_SCRIPT_NAME).exists())

    def test_new_entry_script_help(self):
        result = self.run_help([sys.executable, NEW_SCRIPT_NAME, "--help"])

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue("Chem-PDF-Extractor" in result.stdout or "--cli" in result.stdout)

    def test_module_entrypoint_still_works(self):
        result = self.run_help([sys.executable, "-m", "chem_pdf_extractor", "--help"])

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue("Chem-PDF-Extractor" in result.stdout or "--cli" in result.stdout)

    def test_readme_no_longer_recommends_old_script(self):
        content = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("python -m chem_pdf_extractor", content)
        self.assertIn(NEW_SCRIPT_NAME, content)
        self.assertNotIn(f"python {OLD_SCRIPT_NAME}", content)

    def test_pyproject_uses_english_script_module(self):
        content = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")

        self.assertIn("run_chem_pdf_extractor", content)
        self.assertIn('include = ["chem_pdf_extractor*"]', content)
        self.assertNotIn('py-modules = ["ShuJuTiQuJiaoBen"]', content)

    def test_ci_compiles_english_script(self):
        content = (REPO_ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")

        self.assertIn(f"python -m py_compile {NEW_SCRIPT_NAME}", content)
        self.assertNotIn(f"python -m py_compile {OLD_SCRIPT_NAME}", content)

    def test_pr_template_uses_english_script(self):
        content = (REPO_ROOT / ".github" / "pull_request_template.md").read_text(encoding="utf-8")

        self.assertIn(f"python -m py_compile {NEW_SCRIPT_NAME}", content)
        self.assertNotIn(f"python -m py_compile {OLD_SCRIPT_NAME}", content)

    def test_windows_package_guide_uses_english_script(self):
        content = (REPO_ROOT / "docs" / "windows_package.md").read_text(encoding="utf-8")

        self.assertIn(NEW_SCRIPT_NAME, content)
        self.assertNotIn(OLD_SCRIPT_NAME, content)

    def test_windows_launchers_do_not_call_old_script_directly(self):
        for launcher in ["Start-Chem-PDF-Extractor.bat", "YiJianQiDong.bat"]:
            with self.subTest(launcher=launcher):
                content = (REPO_ROOT / launcher).read_text(encoding="utf-8")
                self.assertNotIn(OLD_SCRIPT_NAME, content)


if __name__ == "__main__":
    unittest.main()
