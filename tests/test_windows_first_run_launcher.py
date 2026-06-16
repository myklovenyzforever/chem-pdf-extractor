import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class WindowsFirstRunLauncherTest(unittest.TestCase):
    def test_bilingual_bat_launchers_delegate_to_shared_powershell(self):
        english = (REPO_ROOT / "Start-Chem-PDF-Extractor.bat").read_text(encoding="utf-8")
        chinese = (REPO_ROOT / "YiJianQiDong.bat").read_text(encoding="utf-8")

        for content in [english, chinese]:
            with self.subTest(launcher=content[:40]):
                self.assertIn("app\\install_and_start.ps1", content)
                self.assertIn("install_and_start.ps1", content)
                self.assertIn("-ExecutionPolicy Bypass", content)
                self.assertIn("-UserRoot", content)
                self.assertIn("CHEM_PDF_EXTRACTOR_USER_ROOT", content)
                self.assertIn("logs", content)
                self.assertIn("EXIT_CODE", content)
                self.assertIn("exit /b %EXIT_CODE%", content)
                self.assertIn("pause", content.lower())
                self.assertNotIn("pip install", content.lower())
                self.assertNotIn("winget", content.lower())
                self.assertNotIn("requirements.txt", content.lower())

        self.assertIn("-Language en", english)
        self.assertIn("Starting Chem-PDF-Extractor", english)
        self.assertIn("Press any key to close this window", english)
        self.assertIn("-Language zh", chinese)
        self.assertIn("正在启动 Chem-PDF-Extractor", chinese)
        self.assertIn("按任意键关闭此窗口", chinese)

    def test_windows_launchers_configure_utf8_console(self):
        english = (REPO_ROOT / "Start-Chem-PDF-Extractor.bat").read_text(encoding="utf-8")
        chinese = (REPO_ROOT / "YiJianQiDong.bat").read_text(encoding="utf-8")
        ps1 = (REPO_ROOT / "install_and_start.ps1").read_text(encoding="utf-8")

        for content in [english, chinese]:
            self.assertIn("chcp 65001", content)
            self.assertIn('set "PYTHONUTF8=1"', content)
            self.assertIn('set "PYTHONIOENCODING=utf-8"', content)

        self.assertIn("[Console]::OutputEncoding", ps1)
        self.assertIn("[Console]::InputEncoding", ps1)
        self.assertIn("$OutputEncoding", ps1)
        self.assertIn('$env:PYTHONIOENCODING = "utf-8"', ps1)

    def test_powershell_launcher_has_backend_menu_and_runtime_flow(self):
        content = (REPO_ROOT / "install_and_start.ps1").read_text(encoding="utf-8")

        self.assertIn("param(", content)
        self.assertIn('[ValidateSet("en", "zh")]', content)
        self.assertIn("[string]$Language", content)
        self.assertIn("[string]$UserRoot", content)
        self.assertIn("$AppRoot", content)
        self.assertIn("$UserRoot", content)
        self.assertIn("$InputDir", content)
        self.assertIn("$OutputDir", content)
        self.assertIn("CHEM_PDF_EXTRACTOR_USER_ROOT", content)
        self.assertIn("CHEM_PDF_EXTRACTOR_LOG_DIR", content)
        self.assertIn("Get-LauncherText", content)
        self.assertIn("Please choose a PDF parsing backend", content)
        self.assertIn("请选择 PDF 解析后端", content)
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

        self.assertNotIn("閺夆晜鍔?", content)
        self.assertNotIn("鏉╂劘", content)
        self.assertIn("bundled_runtime", content)
        self.assertIn(".venv\\Scripts\\python.exe", content)
        self.assertIn("YiLaiHuanJing", content)
        self.assertIn("运行依赖", content)
        self.assertNotIn("杩愯渚濊禆", content)

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
