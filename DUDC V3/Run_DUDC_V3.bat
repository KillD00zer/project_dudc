@echo off
setlocal EnableExtensions
title DUDC V3 - Cadastral Certificate Workflow Studio
cls
cd /d "%~dp0"

echo ======================================================================
echo   DUDC V3 - Cadastral Certificate Workflow Studio
echo ======================================================================
echo.

REM Ensure app shortcut exists with custom icon
if not exist "DUDC V3 Studio.lnk" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$w=New-Object -ComObject WScript.Shell;$s=$w.CreateShortcut((Join-Path (Get-Location).Path 'DUDC V3 Studio.lnk'));$s.TargetPath=(Join-Path (Get-Location).Path 'Run_DUDC_V3.bat');$s.WorkingDirectory=(Get-Location).Path;$s.IconLocation=(Join-Path (Get-Location).Path 'assets\app_icon.ico,0');$s.Description='DUDC V3 - Cadastral Certificate Workflow Studio';$s.Save()" >nul 2>&1
)

REM Kill any stale server on port 8765
for /f "tokens=5" %%a in ('netstat -ano ^| findstr "127.0.0.1:8765" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)
ping -n 2 127.0.0.1 > nul

REM Detect Python
set "PY_CMD="

if exist "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" (
    set "PY_CMD=C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"
    goto py_found
)

where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PY_CMD=python"
    goto py_found
)

where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PY_CMD=py"
    goto py_found
)

for /d %%d in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%d\python.exe" (
        set "PY_CMD=%%d\python.exe"
        goto py_found
    )
)

for /d %%d in ("C:\Python3*") do (
    if exist "%%d\python.exe" (
        set "PY_CMD=%%d\python.exe"
        goto py_found
    )
)

for /d %%d in ("%ProgramFiles%\Python3*") do (
    if exist "%%d\python.exe" (
        set "PY_CMD=%%d\python.exe"
        goto py_found
    )
)

:py_missing
echo.
echo ======================================================================
echo [ERROR] Python not found on this computer!
echo.
echo Please install Python 3.10 or newer from https://www.python.org/
echo Make sure to check: "Add python.exe to PATH" during installation.
echo Or run Install_Dependencies.bat once Python is installed.
echo ======================================================================
echo.
pause
exit /b 1

:py_found
echo [INFO] Using Python: %PY_CMD%

REM Check dependencies
"%PY_CMD%" -c "import pandas, openpyxl, xlrd, pyproj, shapely, PIL, numpy, matplotlib, arabic_reshaper, bidi" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo.
    echo ======================================================================
    echo [NOTICE] Required libraries are missing. Installing now...
    echo ======================================================================
    echo.
    "%PY_CMD%" -m pip install -r "%~dp0requirements.txt"
    if %ERRORLEVEL% neq 0 (
        echo.
        echo [ERROR] Failed to install dependencies automatically.
        echo Please run Install_Dependencies.bat or check your internet connection.
        echo.
        pause
        exit /b 1
    )
)

echo [INFO] Starting DUDC Application Server...
"%PY_CMD%" "%~dp0app_server.py"

if %ERRORLEVEL% neq 0 (
    echo.
    echo ======================================================================
    echo [ERROR] Application server exited with code %ERRORLEVEL%.
    echo Check the error messages above.
    echo ======================================================================
    echo.
    pause
)
