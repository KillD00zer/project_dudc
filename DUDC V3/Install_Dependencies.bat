@echo off
setlocal EnableExtensions
title DUDC V4.0 - Dependencies Installer
cls
cd /d "%~dp0"

echo ======================================================================
echo   DUDC V4.0 - Dependencies Installer
echo ======================================================================
echo.

REM Detect Python (1. Check Portable Runtime first)
set "PY_CMD="

if exist "%~dp0runtime\python.exe" (
    echo ======================================================================
    echo   [INFO] Pre-bundled Portable 32-bit Runtime detected!
    echo   All dependencies are already bundled and verified.
    echo ======================================================================
    echo.
    set /p LAUNCH="Do you want to launch DUDC V3 now? (Y/N, default Y): "
    if /i not "%LAUNCH%"=="N" call "%~dp0Run_DUDC_V3.bat"
    exit /b 0
)

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

REM ------------------------------------------------------------------
REM Step 1: Check & Setup Git (for GitHub in-app updates)
REM ------------------------------------------------------------------
echo [1/4] Checking Git installation...
set "GIT_CMD="

where git >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "GIT_CMD=git"
    goto git_ok
)
if exist "C:\Program Files\Git\cmd\git.exe" (
    set "GIT_CMD=C:\Program Files\Git\cmd\git.exe"
    set "PATH=C:\Program Files\Git\cmd;%PATH%"
    goto git_ok
)
if exist "%LOCALAPPDATA%\Programs\Git\cmd\git.exe" (
    set "GIT_CMD=%LOCALAPPDATA%\Programs\Git\cmd\git.exe"
    set "PATH=%LOCALAPPDATA%\Programs\Git\cmd;%PATH%"
    goto git_ok
)

echo [NOTICE] Git is not installed on this system.
echo [INFO] Attempting automatic Git installation for non-technical setup...

REM Try winget (Windows Package Manager - built-in on Win10/11)
where winget >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [INFO] Installing Git via Windows Package Manager (winget)...
    winget install --id Git.Git -e --source winget --silent --accept-source-agreements --accept-package-agreements >nul 2>&1
    if %ERRORLEVEL% equ 0 goto check_git_installed
)

REM Fallback: Download official installer silently via PowerShell
echo [INFO] Downloading official Git for Windows installer...
set "GIT_SETUP_EXE=%TEMP%\Git_Silent_Setup.exe"
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('https://github.com/git-for-windows/git/releases/latest/download/Git-64-bit.exe', '%GIT_SETUP_EXE%')" >nul 2>&1
if exist "%GIT_SETUP_EXE%" (
    echo [INFO] Installing Git silently in the background...
    start /wait "" "%GIT_SETUP_EXE%" /VERYSILENT /NORESTART /NOCANCEL /SP- /CLOSEAPPLICATIONS
    del /f /q "%GIT_SETUP_EXE%" >nul 2>&1
)

:check_git_installed
if exist "C:\Program Files\Git\cmd\git.exe" (
    set "GIT_CMD=C:\Program Files\Git\cmd\git.exe"
    set "PATH=C:\Program Files\Git\cmd;%PATH%"
) else if exist "%LOCALAPPDATA%\Programs\Git\cmd\git.exe" (
    set "GIT_CMD=%LOCALAPPDATA%\Programs\Git\cmd\git.exe"
    set "PATH=%LOCALAPPDATA%\Programs\Git\cmd;%PATH%"
) else (
    where git >nul 2>&1
    if %ERRORLEVEL% equ 0 set "GIT_CMD=git"
)

if defined GIT_CMD (
    echo [SUCCESS] Git installed and configured successfully!
) else (
    echo [WARNING] Git could not be installed automatically.
    echo [NOTE] DUDC will work normally, but GitHub auto-updates will be disabled.
)
goto git_step_done

:git_ok
echo [INFO] Detected Git:
"%GIT_CMD%" --version

:git_step_done
echo.

REM ------------------------------------------------------------------
REM Step 2: Check pip
REM ------------------------------------------------------------------
echo [2/4] Checking pip...
"%PY_CMD%" -m pip --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [INFO] Bootstrapping pip...
    "%PY_CMD%" -m ensurepip --upgrade >nul 2>&1
    "%PY_CMD%" -m pip --version >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [INFO] Downloading get-pip.py to install pip...
        powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('https://bootstrap.pypa.io/get-pip.py', '%TEMP%\get-pip.py')" >nul 2>&1
        if exist "%TEMP%\get-pip.py" (
            "%PY_CMD%" "%TEMP%\get-pip.py" --user >nul 2>&1
            del /f /q "%TEMP%\get-pip.py" >nul 2>&1
        )
    )
)

"%PY_CMD%" -m pip --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo.
    echo ======================================================================
    echo [ERROR] Python pip is missing and could not be bootstrapped automatically.
    echo Please reinstall Python and check "pip", or run as Administrator.
    echo ======================================================================
    echo.
    pause
    exit /b 1
)

echo.
REM ------------------------------------------------------------------
REM Step 3: Installing dependencies
REM ------------------------------------------------------------------
echo [3/4] Installing dependencies from requirements.txt...
echo ----------------------------------------------------------------------
set "REQ_FILE="
if exist "%~dp0requirements.txt" set "REQ_FILE=%~dp0requirements.txt"
if not defined REQ_FILE if exist "requirements.txt" set "REQ_FILE=requirements.txt"

"%PY_CMD%" -m pip install -r "%REQ_FILE%"
if %ERRORLEVEL% neq 0 (
    echo [INFO] Retrying with --user permissions...
    "%PY_CMD%" -m pip install --user -r "%REQ_FILE%"
)
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
REM ------------------------------------------------------------------
REM Step 4: Verify installed modules
REM ------------------------------------------------------------------
echo [4/4] Verifying all installed modules...
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
