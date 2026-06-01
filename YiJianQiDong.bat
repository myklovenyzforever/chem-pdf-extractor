@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "LOCAL_PYTHON=%SCRIPT_DIR%YiLaiHuanJing\python\python.exe"
set "APP_SCRIPT=%SCRIPT_DIR%ShuJuTiQuJiaoBen.py"

if not exist "%APP_SCRIPT%" (
  echo Script was not found:
  echo "%APP_SCRIPT%"
  pause
  exit /b 1
)

if exist "%LOCAL_PYTHON%" (
  set "PYTHON_EXE=%LOCAL_PYTHON%"
) else (
  echo Local runtime was not found. Falling back to system python.
  set "PYTHON_EXE=python"
)

"%PYTHON_EXE%" "%APP_SCRIPT%"
echo.
echo Program exited. Press any key to close this window.
pause >nul
