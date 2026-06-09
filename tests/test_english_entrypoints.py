import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class EnglishEntrypointsTest(unittest.TestCase):
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

    def test_python_module_entrypoint_help(self):
        result = self.run_help([sys.executable, "-m", "chem_pdf_extractor", "--help"])

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue("Chem-PDF-Extractor" in result.stdout or "--cli" in result.stdout)

    def test_script_entry_help(self):
        result = self.run_help([sys.executable, "run_chem_pdf_extractor.py", "--help"])

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue("Chem-PDF-Extractor" in result.stdout or "--cli" in result.stdout)

    def test_new_windows_launcher_exists_and_uses_module_entrypoint(self):
        content = (REPO_ROOT / "Start-Chem-PDF-Extractor.bat").read_text(encoding="utf-8")

        self.assertTrue("-m %APP_MODULE%" in content or "-m chem_pdf_extractor" in content)
        self.assertIn("bundled_runtime", content)
        self.assertIn("YiLaiHuanJing", content)
        self.assertIn("logs", content)
        self.assertIn("ERRORLEVEL", content)
        self.assertIn("pause", content.lower())

    def test_legacy_windows_launcher_delegates_to_new_launcher(self):
        content = (REPO_ROOT / "YiJianQiDong.bat").read_text(encoding="utf-8")

        self.assertIn("Start-Chem-PDF-Extractor.bat", content)
        self.assertIn("call", content.lower())
        self.assertIn("ERRORLEVEL", content)

    def test_readme_prefers_python_module_entrypoint(self):
        content = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("python -m chem_pdf_extractor", content)
        self.assertIn("run_chem_pdf_extractor.py", content)
        self.assertNotIn("python ShuJuTiQuJiaoBen.py", content)

    def test_windows_package_guide_prefers_english_launcher(self):
        content = (REPO_ROOT / "docs" / "windows_package.md").read_text(encoding="utf-8")

        self.assertIn("Start-Chem-PDF-Extractor.bat", content)
        self.assertIn("run_chem_pdf_extractor.py", content)
        self.assertIn("bundled_runtime/", content)
        self.assertIn("YiJianQiDong.bat", content)
        self.assertIn("YiLaiHuanJing/", content)
        self.assertNotIn("ShuJuTiQuJiaoBen.py", content)
        self.assertRegex(content, r"[Ll]egacy")

    def test_gitignore_ignores_new_runtime_directory(self):
        content = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")

        self.assertIn("bundled_runtime/", content)
        self.assertIn("YiLaiHuanJing/", content)

    def test_config_runtime_names_include_english_and_legacy(self):
        from chem_pdf_extractor.config import (
            BUNDLED_RUNTIME_DIR_NAME,
            LEGACY_BUNDLED_RUNTIME_DIR_NAMES,
        )

        self.assertEqual(BUNDLED_RUNTIME_DIR_NAME, "bundled_runtime")
        self.assertIn("YiLaiHuanJing", LEGACY_BUNDLED_RUNTIME_DIR_NAMES)
        self.assertIn("运行依赖", LEGACY_BUNDLED_RUNTIME_DIR_NAMES)


if __name__ == "__main__":
    unittest.main()
