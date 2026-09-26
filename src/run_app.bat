@echo off
chcp 65001 > nul
title Cadastral Survey Certificate Generator V2
cls
cd /d "%~dp0"
echo ======================================================================
echo   Cadastral Survey Certificate Generator V2
echo   Dakahlia Utility Data Center - Source Server Launcher
echo ======================================================================
echo.

set "ARCPY=C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"
if exist "%ARCPY%" (
    echo ArcGIS Pro Python detected. Starting local server...
    "%ARCPY%" "%~dp0app_server.py"
    goto end
)

where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo Python detected. Starting local server...
    python "%~dp0app_server.py"
    goto end
)

echo [WARNING] Python 3 was not found on your system PATH.
echo.
pause

:end
