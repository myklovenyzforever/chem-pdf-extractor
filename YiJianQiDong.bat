@echo off
chcp 65001 >nul
setlocal
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

set "USER_ROOT=%~dp0"
cd /d "%USER_ROOT%"

set "CHEM_PDF_EXTRACTOR_LAUNCHER_LANGUAGE=zh"
set "CHEM_PDF_EXTRACTOR_USER_ROOT=%USER_ROOT%"
set "CHEM_PDF_EXTRACTOR_LOG_DIR=%USER_ROOT%logs"
set "LOG_DIR=%USER_ROOT%logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

set "PS_SCRIPT=%USER_ROOT%app\install_and_start.ps1"
if not exist "%PS_SCRIPT%" set "PS_SCRIPT=%USER_ROOT%install_and_start.ps1"

echo.
echo 正在启动 Chem-PDF-Extractor...
echo 用户目录: "%USER_ROOT%"
echo 日志目录: "%LOG_DIR%"

if not exist "%PS_SCRIPT%" (
  echo.
  echo 未找到共享启动脚本。
  echo 打包路径应为: "%USER_ROOT%app\install_and_start.ps1"
  echo 源码路径应为: "%USER_ROOT%install_and_start.ps1"
  echo.
  echo 按任意键关闭此窗口。
  pause >nul
  exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%" -Language zh -UserRoot "%USER_ROOT%"
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo Chem-PDF-Extractor 启动器退出代码: %EXIT_CODE%
echo 安装日志: "%LOG_DIR%\install.log"
echo 启动日志: "%LOG_DIR%\startup.log"
echo 崩溃日志: "%LOG_DIR%\crash.log"
echo 任务日志: "%LOG_DIR%\task.log"
echo.
echo 按任意键关闭此窗口。
pause >nul

exit /b %EXIT_CODE%
