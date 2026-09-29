@echo off
setlocal EnableExtensions
title DUDC V3 - Dependencies Installer
cls
cd /d "%~dp0"

echo ======================================================================
echo   DUDC V3 - Dependencies Installer
echo ======================================================================
echo.

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
echo [ERROR] Python was not found on this computer!
echo ======================================================================
echo.
echo Please follow these simple steps to install Python:
echo   1. Download Python 3.10+ from: https://www.python.org/downloads/
echo   2. During installation, CHECK THE BOX:
echo      [x] "Add python.exe to PATH"
echo   3. Once installed, re-run this file (Install_Dependencies.bat).
echo.
pause
exit /b 1

:py_found
echo [INFO] Detected Python: %PY_CMD%
echo.

echo [1/3] Checking pip...
"%PY_CMD%" -m pip --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [INFO] Bootstrapping pip...
    "%PY_CMD%" -m ensurepip --upgrade >nul 2>&1
)

echo.
echo [2/3] Installing dependencies from requirements.txt...
echo ----------------------------------------------------------------------
"%PY_CMD%" -m pip install -r "%~dp0requirements.txt"
if %ERRORLEVEL% neq 0 (
    echo.
    echo ======================================================================
    echo [ERROR] Dependency installation encountered an issue.
    echo Please verify your internet connection or run as Administrator.
    echo ======================================================================
    echo.
    pause
    exit /b 1
)

echo.
echo [3/3] Verifying all installed modules...
echo ----------------------------------------------------------------------
"%PY_CMD%" -c "import pandas, openpyxl, xlrd, pyproj, shapely, PIL, numpy, matplotlib, arabic_reshaper, bidi; print('ALL_DEPENDENCIES_VERIFIED_SUCCESSFULLY')"
if %ERRORLEVEL% neq 0 (
    echo.
    echo ======================================================================
    echo [ERROR] Verification failed. Some packages could not be imported.
    echo ======================================================================
    echo.
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo   [SUCCESS] All required dependencies are installed and verified!
echo ======================================================================
echo.
set /p LAUNCH="Do you want to launch DUDC V3 now? (Y/N, default Y): "
if /i "%LAUNCH%"=="N" goto end

call "%~dp0Run_DUDC_V3.bat"

:end
