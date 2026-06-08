@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "LOCAL_PYTHON=%SCRIPT_DIR%YiLaiHuanJing\python\python.exe"
set "APP_SCRIPT=%SCRIPT_DIR%ShuJuTiQuJiaoBen.py"
set "LOG_DIR=%SCRIPT_DIR%logs"
set "CHEM_PDF_EXTRACTOR_LOG_DIR=%LOG_DIR%"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

if not exist "%APP_SCRIPT%" (
  echo Script was not found:
  echo "%APP_SCRIPT%"
  echo.
  echo Startup log: "%LOG_DIR%\startup.log"
  echo Crash log: "%LOG_DIR%\crash.log"
  echo Task log: "%LOG_DIR%\task.log"
  pause
  exit /b 1
)

if exist "%LOCAL_PYTHON%" (
  set "PYTHON_EXE=%LOCAL_PYTHON%"
) else (
  echo Local runtime was not found. Falling back to system python.
  set "PYTHON_EXE=python"
)

>>"%LOG_DIR%\startup.log" echo [%DATE% %TIME%] bat startup
>>"%LOG_DIR%\startup.log" echo Script dir: "%SCRIPT_DIR%"
>>"%LOG_DIR%\startup.log" echo Python exe: "%PYTHON_EXE%"

"%PYTHON_EXE%" "%APP_SCRIPT%"
set "EXIT_CODE=%ERRORLEVEL%"
echo.
echo Program exited with code: %EXIT_CODE%
echo Startup log: "%LOG_DIR%\startup.log"
echo Crash log: "%LOG_DIR%\crash.log"
echo Task log: "%LOG_DIR%\task.log"
echo.
echo Press any key to close this window.
pause >nul
exit /b %EXIT_CODE%
