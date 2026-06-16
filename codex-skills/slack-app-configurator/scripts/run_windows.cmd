@echo off
setlocal

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 "%~dp0slack_app_configurator.py" --open %*
  exit /b %ERRORLEVEL%
)

where python >nul 2>nul
if %ERRORLEVEL%==0 (
  python "%~dp0slack_app_configurator.py" --open %*
  exit /b %ERRORLEVEL%
)

where python3 >nul 2>nul
if %ERRORLEVEL%==0 (
  python3 "%~dp0slack_app_configurator.py" --open %*
  exit /b %ERRORLEVEL%
)

echo Python 3 was not found. Install Python 3, then run this script again.
exit /b 1
