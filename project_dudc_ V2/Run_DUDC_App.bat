@echo off
chcp 65001 > nul
title Project DUDC - Cadastral Survey Certificate Generator V2
cls
cd /d "%~dp0"
echo ======================================================================
echo   Project DUDC - Cadastral Survey Certificate Generator V2
echo   Dakahlia Utility Data Center
echo.
echo   Starting application with Anti-Forgery Security & Watermark...
echo ======================================================================

set "ARCPY=C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"
if exist "%ARCPY%" if exist "%~dp0..\src\app_server.py" (
    echo Starting live updated application...
    "%ARCPY%" "%~dp0..\src\app_server.py"
    goto end
)

start "" "%~dp0Certificate_Generator.exe"

:end
