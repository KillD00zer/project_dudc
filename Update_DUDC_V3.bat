@echo off
setlocal EnableExtensions
chcp 65001 > nul
title DUDC V4.0 - System Updater (GitHub)
cls
cd /d "%~dp0"

echo ======================================================================
echo   DUDC V4.0 - GitHub System Updater
echo ======================================================================
echo.

REM Verify Git and check common paths
where git >nul 2>&1
if %ERRORLEVEL% neq 0 (
    if exist "C:\Program Files\Git\cmd\git.exe" set "PATH=C:\Program Files\Git\cmd;%PATH%"
    if exist "%ProgramFiles%\Git\cmd\git.exe" set "PATH=%ProgramFiles%\Git\cmd;%PATH%"
    if exist "%LOCALAPPDATA%\Programs\Git\cmd\git.exe" set "PATH=%LOCALAPPDATA%\Programs\Git\cmd;%PATH%"
)

where git >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Git is not installed on this computer or not in PATH.
    echo Please install Git from: https://git-scm.com/
    echo.
    pause
    exit /b 1
)

echo [1/3] Connecting to GitHub and checking for updates...
git fetch origin main >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Could not connect to GitHub. Please check your internet connection.
    echo.
    pause
    exit /b 1
)

set "LOCAL_HASH="
set "REMOTE_HASH="
for /f %%a in ('git rev-parse --short HEAD') do set "LOCAL_HASH=%%a"
for /f %%a in ('git rev-parse --short origin/main') do set "REMOTE_HASH=%%a"

echo [2/3] Current installed version: [%LOCAL_HASH%]
echo       Latest version on GitHub:  [%REMOTE_HASH%]
echo.

if "%LOCAL_HASH%"=="%REMOTE_HASH%" (
    echo ======================================================================
    echo   The system is completely up-to-date! You are on the latest commit.
    echo ======================================================================
    echo.
    pause
    exit /b 0
)

echo ======================================================================
echo   New update available! Recent commits:
echo ======================================================================
echo.
git log HEAD..origin/main --pretty=format:"* %s [%h] (%cr)"
echo.
echo ======================================================================
echo.

set /p CONFIRM="Do you want to pull and apply this update now? (Y/N, default Y): "
if /i "%CONFIRM%"=="N" (
    echo Update cancelled.
    pause
    exit /b 0
)

echo.
echo [3/3] Pulling and applying updates (git pull)...
echo ----------------------------------------------------------------------
git pull origin main

if %ERRORLEVEL% neq 0 (
    echo.
    echo [NOTICE] Local changes detected. Stashing changes and retrying pull...
    git stash >nul 2>&1
    git pull origin main
)

if %ERRORLEVEL% neq 0 (
    echo [NOTICE] Cleaning tracked files and retrying pull...
    git checkout -- . >nul 2>&1
    git pull origin main
)

if %ERRORLEVEL% equ 0 (
    echo.
    echo ======================================================================
    echo   [SUCCESS] System updated successfully to the latest version!
    echo ======================================================================
) else (
    echo.
    echo [ERROR] Could not complete update. Please review errors above.
)

echo.
pause
