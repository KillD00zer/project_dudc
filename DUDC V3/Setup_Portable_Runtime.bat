@echo off
setlocal EnableExtensions
title DUDC V3 - Portable 32-bit Runtime Setup
cls
cd /d "%~dp0"

echo ======================================================================
echo   DUDC V3 - Standalone Portable 32-bit Runtime Setup
echo ======================================================================
echo.

if exist "runtime\python.exe" (
    echo [INFO] Portable runtime already exists in: %~dp0runtime\
    echo Checking verification...
    "%~dp0runtime\python.exe" -c "import pandas, numpy, shapely, pyproj, matplotlib, PIL, openpyxl, xlrd, arabic_reshaper, bidi; print('ALL_MODULES_OK')" >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        echo [SUCCESS] Portable 32-bit environment is healthy and verified!
        pause
        exit /b 0
    )
)

echo [1/3] Downloading official Python 3.11 32-bit Embeddable Package...
set "TEMP_ZIP=%TEMP%\python_embed_32.zip"
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-win32.zip', '%TEMP_ZIP%')"
if not exist "%TEMP_ZIP%" (
    echo [ERROR] Failed to download Python embeddable package.
    pause
    exit /b 1
)

echo [2/3] Extracting runtime to %~dp0runtime\...
if not exist "runtime" mkdir "runtime"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Path '%TEMP_ZIP%' -DestinationPath '%~dp0runtime' -Force"
del /f /q "%TEMP_ZIP%" >nul 2>&1

REM Configure ._pth for site-packages and app root
powershell -NoProfile -ExecutionPolicy Bypass -Command "$c = Get-Content '%~dp0runtime\python311._pth'; $c = $c -replace '#import site', 'import site'; $c += '..'; $c += 'Lib\site-packages'; Set-Content '%~dp0runtime\python311._pth' $c"

echo [3/3] Installing pre-compiled 32-bit GIS and Mathematics wheels...
set "GET_PIP=%TEMP%\get-pip.py"
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('https://bootstrap.pypa.io/get-pip.py', '%GET_PIP%')"
"%~dp0runtime\python.exe" "%GET_PIP%" --no-warn-script-location >nul 2>&1
del /f /q "%GET_PIP%" >nul 2>&1

"%~dp0runtime\python.exe" -m pip install --no-warn-script-location "kiwisolver<=1.4.7" "numpy==1.26.4" "pandas==2.0.3" "matplotlib==3.7.5" "shapely" "pyproj" "pillow" "openpyxl" "xlrd" "arabic-reshaper" "python-bidi==0.4.2"

echo.
echo ======================================================================
echo   [SUCCESS] Standalone Portable 32-bit Runtime is completely ready!
echo ======================================================================
echo.
pause
