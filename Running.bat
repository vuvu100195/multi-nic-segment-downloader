@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_CMD="

where py >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py -3"
) else (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        set "PYTHON_CMD=python"
    )
)

if not defined PYTHON_CMD (
    echo.
    echo [ERROR] Python 3 was not found.
    echo Install Python 3.10 or newer from:
    echo https://www.python.org/downloads/windows/
    echo Select "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating a local Python environment...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 goto :venv_error

    echo Installing required libraries...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto :install_error
)

".venv\Scripts\python.exe" main.py
if errorlevel 1 goto :app_error
goto :end

:venv_error
echo.
echo [ERROR] Could not create .venv.
echo Ensure that Python includes the venv module.
goto :pause_exit

:install_error
echo.
echo [ERROR] Could not install required libraries.
echo Check your Internet connection or proxy/firewall settings.
goto :pause_exit

:app_error
echo.
echo [ERROR] The application stopped with an error.
echo Copy the error above and report it through GitHub Issues.

:pause_exit
pause

:end
endlocal