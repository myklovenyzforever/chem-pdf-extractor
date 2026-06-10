@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "PS_SCRIPT=%SCRIPT_DIR%install_and_start.ps1"
set "LOG_DIR=%SCRIPT_DIR%logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo.
echo Starting Chem-PDF-Extractor...

if not exist "%PS_SCRIPT%" (
  echo.
  echo install_and_start.ps1 was not found.
  echo Expected: "%PS_SCRIPT%"
  echo.
  echo Press any key to close this window.
  pause >nul
  exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
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
