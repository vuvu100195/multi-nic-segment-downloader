@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

title Multi-NIC Segment Downloader Launcher

set "PYTHON_EXE="

where py >nul 2>nul
if not errorlevel 1 (
    for /f "delims=" %%P in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%P"
)

if not defined PYTHON_EXE (
    where python >nul 2>nul
    if not errorlevel 1 (
        for /f "delims=" %%P in ('python -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%P"
    )
)

if not defined PYTHON_EXE (
    echo.
    echo [ERROR] Python 3 was not found.
    echo.
    echo Install Python 3.13.1 or newer, 64-bit, from:
    echo https://www.python.org/downloads/windows/
    echo.
    echo During installation, select:
    echo   - Add python.exe to PATH
    echo   - pip
    echo   - Tcl/Tk and IDLE
    echo   - Python Launcher / py launcher
    echo.
    goto :pause_exit
)

for /f "tokens=2" %%V in ('"%PYTHON_EXE%" --version 2^>^&1') do set "PY_VERSION=%%V"

if "%PY_VERSION%"=="3.13.0" (
    echo.
    echo [ERROR] Python 3.13.0 is not supported.
    echo Python 3.13.0 has a known Tkinter/Tcl issue in Windows virtual environments.
    echo Please install Python 3.13.1 or newer, 64-bit.
    echo.
    goto :pause_exit
)

if not exist "main.py" (
    echo.
    echo [ERROR] main.py was not found.
    echo Keep Running.bat in the same folder as main.py.
    echo.
    goto :pause_exit
)

if not exist "requirements.txt" (
    echo.
    echo [ERROR] requirements.txt was not found.
    echo Keep Running.bat in the same folder as requirements.txt.
    echo.
    goto :pause_exit
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating local Python environment .venv ...
    "%PYTHON_EXE%" -m venv .venv
    if errorlevel 1 goto :venv_error

    echo Installing required Python packages ...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    if errorlevel 1 goto :install_error

    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto :install_error
)

".venv\Scripts\python.exe" -c "import tkinter as tk; root=tk.Tk(); root.withdraw(); root.destroy()" >nul 2>nul
if errorlevel 1 goto :tkinter_error

".venv\Scripts\python.exe" main.py
set "APP_EXIT=!errorlevel!"

if not "!APP_EXIT!"=="0" goto :app_error
goto :end

:venv_error
echo.
echo [ERROR] Could not create the local .venv environment.
goto :pause_exit

:install_error
echo.
echo [ERROR] Could not install required Python packages.
echo Check the Internet connection, firewall, proxy, or Python/pip installation.
goto :pause_exit

:tkinter_error
echo.
echo [ERROR] Tkinter or Tcl/Tk is missing, broken, or unavailable.
echo Install Python 3.13.1 or newer with Tcl/Tk and IDLE selected.
echo If Python was just updated, delete .venv and run this file again.
goto :pause_exit

:app_error
echo.
echo [ERROR] The application stopped with an error.
echo Read the traceback above and report it through GitHub Issues.
goto :pause_exit

:pause_exit
echo.
pause
exit /b 1

:end
endlocal
exit /b 0
