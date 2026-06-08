@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "LOG_DIR=%SCRIPT_DIR%logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "CHEM_PDF_EXTRACTOR_LOG_DIR=%LOG_DIR%"

set "APP_MODULE=chem_pdf_extractor"
set "PYTHON_NEW_RUNTIME=%SCRIPT_DIR%bundled_runtime\python\python.exe"
set "PYTHON_LEGACY_RUNTIME=%SCRIPT_DIR%YiLaiHuanJing\python\python.exe"
set "PYTHON_LEGACY_RUNTIME_CN=%SCRIPT_DIR%运行依赖\python\python.exe"

echo.>> "%LOG_DIR%\startup.log"
echo ===== Windows launcher started =====>> "%LOG_DIR%\startup.log"
echo date: %DATE% %TIME%>> "%LOG_DIR%\startup.log"
echo script_dir: %SCRIPT_DIR%>> "%LOG_DIR%\startup.log"

if exist "%PYTHON_NEW_RUNTIME%" (
  set "PYTHON_EXE=%PYTHON_NEW_RUNTIME%"
) else if exist "%PYTHON_LEGACY_RUNTIME%" (
  set "PYTHON_EXE=%PYTHON_LEGACY_RUNTIME%"
) else if exist "%PYTHON_LEGACY_RUNTIME_CN%" (
  set "PYTHON_EXE=%PYTHON_LEGACY_RUNTIME_CN%"
) else (
  echo Bundled runtime was not found. Falling back to system python.
  set "PYTHON_EXE=python"
)

echo python_exe: %PYTHON_EXE%>> "%LOG_DIR%\startup.log"

"%PYTHON_EXE%" -m %APP_MODULE%
set "EXIT_CODE=%ERRORLEVEL%"

echo.>> "%LOG_DIR%\startup.log"
echo process_exit_code: %EXIT_CODE%>> "%LOG_DIR%\startup.log"

echo.
echo Program exited with code: %EXIT_CODE%
echo Startup log: "%LOG_DIR%\startup.log"
echo Crash log: "%LOG_DIR%\crash.log"
echo Task log: "%LOG_DIR%\task.log"
echo.
echo Press any key to close this window.
pause >nul

exit /b %EXIT_CODE%
