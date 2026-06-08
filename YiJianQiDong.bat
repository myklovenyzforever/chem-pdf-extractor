@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "NEW_LAUNCHER=%SCRIPT_DIR%Start-Chem-PDF-Extractor.bat"
set "LOG_DIR=%SCRIPT_DIR%logs"

if exist "%NEW_LAUNCHER%" (
  call "%NEW_LAUNCHER%" %*
  exit /b %ERRORLEVEL%
)

echo Start-Chem-PDF-Extractor.bat was not found.
echo Please check that the package is complete.
echo Startup log: "%LOG_DIR%\startup.log"
echo Crash log: "%LOG_DIR%\crash.log"
echo Task log: "%LOG_DIR%\task.log"
pause
exit /b 1
