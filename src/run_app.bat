@echo off
chcp 65001 > nul
title Cadastral Survey Certificate Generator
cls
cd /d "%~dp0"
echo ======================================================================
echo   Cadastral Survey Certificate Generator
echo   Dakahlia Utility Data Center - Source Server Launcher
echo ======================================================================
echo.

where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo Python detected. Starting local server...
    python "%~dp0app_server.py"
    goto end
)

set "ARCPY=C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"
if exist "%ARCPY%" (
    echo ArcGIS Pro Python detected. Starting local server...
    "%ARCPY%" "%~dp0app_server.py"
    goto end
)

echo [WARNING] Python 3 was not found on your system PATH.
echo To run this application without installing Python, please use:
echo   Run_DUDC_App.bat
echo located in the 'project_dudc' portable folder.
echo.
pause

:end
