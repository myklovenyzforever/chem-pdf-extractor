import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class WindowsFirstRunLauncherTest(unittest.TestCase):
    def test_bat_delegates_to_install_and_start_powershell(self):
        content = (REPO_ROOT / "Start-Chem-PDF-Extractor.bat").read_text(encoding="utf-8")

        self.assertIn("install_and_start.ps1", content)
        self.assertIn("-ExecutionPolicy Bypass", content)
        self.assertIn("pause", content.lower())

    def test_windows_launchers_configure_utf8_console(self):
        bat = (REPO_ROOT / "Start-Chem-PDF-Extractor.bat").read_text(encoding="utf-8")
        ps1 = (REPO_ROOT / "install_and_start.ps1").read_text(encoding="utf-8")

        self.assertIn("chcp 65001", bat)
        self.assertIn('set "PYTHONUTF8=1"', bat)
        self.assertIn('set "PYTHONIOENCODING=utf-8"', bat)

        self.assertIn("[Console]::OutputEncoding", ps1)
        self.assertIn("[Console]::InputEncoding", ps1)
        self.assertIn("$OutputEncoding", ps1)
        self.assertIn('$env:PYTHONIOENCODING = "utf-8"', ps1)

    def test_powershell_launcher_has_backend_menu_and_runtime_flow(self):
        content = (REPO_ROOT / "install_and_start.ps1").read_text(encoding="utf-8")

        self.assertIn("Please choose a PDF parsing backend", content)
        self.assertIn("[1] pypdf_text", content)
        self.assertIn("[2] pymupdf4llm (recommended)", content)
        self.assertIn("[3] mineru", content)
        self.assertIn(".runtime", content)
        self.assertIn("launcher_settings.json", content)
        self.assertIn(".venv\\Scripts\\python.exe", content)
        self.assertIn("Python.Python.3.11", content)
        self.assertIn("--pdf-mode", content)
        self.assertIn("--open-browser", content)
        self.assertIn("MINERU_COMMAND", content)
        self.assertIn("mineru.exe", content)

    def test_powershell_launcher_runtime_candidates_are_not_mojibake(self):
        content = (REPO_ROOT / "install_and_start.ps1").read_text(encoding="utf-8")

        self.assertNotIn("鏉╂劘", content)
        self.assertIn("bundled_runtime", content)
        self.assertIn(".venv\\Scripts\\python.exe", content)
        self.assertIn("YiLaiHuanJing", content)
        self.assertIn("杩愯渚濊禆", content)

    def test_launcher_installs_expected_requirements_by_backend(self):
        content = (REPO_ROOT / "install_and_start.ps1").read_text(encoding="utf-8")

        self.assertIn("requirements-core.txt", content)
        self.assertIn("requirements.txt", content)
        self.assertIn("requirements-mineru.txt", content)
        self.assertIn("pip\", \"install\", \"--upgrade\", \"uv", content)
        self.assertIn("uv", content)
        self.assertIn("MinerU installation failed", content)
        self.assertIn("Start-Process", content)
        self.assertIn("RedirectStandardOutput", content)
        self.assertIn("RedirectStandardError", content)
        self.assertIn("[1] Retry MinerU installation", content)
        self.assertIn("[2] Continue now with pymupdf4llm", content)
        self.assertIn("[3] Exit", content)

    def test_requirements_mineru_is_optional(self):
        content = (REPO_ROOT / "requirements-mineru.txt").read_text(encoding="utf-8")
        workflow = (REPO_ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")

        self.assertIn("mineru", content.lower())
        self.assertNotIn("requirements-mineru.txt", workflow)

    def test_gitignore_excludes_local_runtime_outputs(self):
        content = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")

        for marker in [".venv/", ".runtime/", "logs/", "config.local.json", ".mineru_outputs/", "wheelhouse/"]:
            self.assertIn(marker, content)

    def test_docs_describe_package_types_and_manual_tests(self):
        content = (REPO_ROOT / "docs" / "windows_package.md").read_text(encoding="utf-8")

        self.assertIn("GitHub Download ZIP", content)
        self.assertIn("Online first-run release package", content)
        self.assertIn("Fully offline package", content)
        self.assertIn("Manual Windows test plan", content)
        self.assertIn("requirements-mineru.txt", content)


if __name__ == "__main__":
    unittest.main()
