@echo off
chcp 65001 > nul
title DUDC V3.5 - Cadastral Certificate Workflow Studio
cls
cd /d "%~dp0"
echo ======================================================================
echo   🏛️ DUDC V3.5 - Cadastral Certificate Workflow Studio
echo   Dakahlia Utility Data Center (مركز معلومات شبكات المرافق)
echo ======================================================================
echo.

set "ARCPY=C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"
if exist "%ARCPY%" (
    echo [INFO] ArcGIS Pro Python detected. Starting DUDC V3.5 Workflow Server...
    "%ARCPY%" "%~dp0app_server.py"
    goto end
)

where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [INFO] Python detected. Starting DUDC V3.5 Workflow Server...
    python "%~dp0app_server.py"
    goto end
)

echo [WARNING] Python 3 was not found on your system PATH.
echo.
pause

:end
