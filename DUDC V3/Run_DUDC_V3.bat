@echo off
chcp 65001 > nul
title DUDC V3.5 - Cadastral Certificate Workflow Studio
cls
cd /d "%~dp0"
echo ======================================================================
echo   DUDC V3.5 - Cadastral Certificate Workflow Studio
echo ======================================================================
echo.

:: Kill any old server instance holding port 8765
for /f "tokens=5" %%a in ('netstat -ano ^| findstr "127.0.0.1:8765" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)
ping -n 2 127.0.0.1 > nul

set "ARCPY=C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"
if exist "%ARCPY%" (
    echo [INFO] Starting with ArcGIS Pro Python...
    "%ARCPY%" "%~dp0app_server.py"
    goto end
)

where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [INFO] Starting with system Python...
    python "%~dp0app_server.py"
    goto end
)

echo [ERROR] Python not found!
pause

:end
