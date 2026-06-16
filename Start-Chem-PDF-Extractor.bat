@echo off
chcp 65001 >nul
setlocal
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

set "USER_ROOT=%~dp0"
cd /d "%USER_ROOT%"

set "CHEM_PDF_EXTRACTOR_LAUNCHER_LANGUAGE=en"
set "CHEM_PDF_EXTRACTOR_USER_ROOT=%USER_ROOT%"
set "CHEM_PDF_EXTRACTOR_LOG_DIR=%USER_ROOT%logs"
set "LOG_DIR=%USER_ROOT%logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

set "PS_SCRIPT=%USER_ROOT%app\install_and_start.ps1"
if not exist "%PS_SCRIPT%" set "PS_SCRIPT=%USER_ROOT%install_and_start.ps1"

echo.
echo Starting Chem-PDF-Extractor...
echo User folder: "%USER_ROOT%"
echo Logs folder: "%LOG_DIR%"

if not exist "%PS_SCRIPT%" (
  echo.
  echo Shared launcher script was not found.
  echo Expected packaged path: "%USER_ROOT%app\install_and_start.ps1"
  echo Expected source path: "%USER_ROOT%install_and_start.ps1"
  echo.
  echo Press any key to close this window.
  pause >nul
  exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%" -Language en -UserRoot "%USER_ROOT%"
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo Chem-PDF-Extractor launcher exited with code: %EXIT_CODE%
echo Install log: "%LOG_DIR%\install.log"
echo Startup log: "%LOG_DIR%\startup.log"
echo Crash log: "%LOG_DIR%\crash.log"
echo Task log: "%LOG_DIR%\task.log"
echo.
echo Press any key to close this window.
pause >nul

exit /b %EXIT_CODE%
