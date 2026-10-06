@echo off
chcp 65001 > nul
cd /d "%~dp0"

REM Ensure root app shortcut exists with custom icon
if not exist "DUDC V4 Studio.lnk" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$w=New-Object -ComObject WScript.Shell;$s=$w.CreateShortcut((Join-Path (Get-Location).Path 'DUDC V4 Studio.lnk'));$s.TargetPath=(Join-Path (Get-Location).Path 'Run_DUDC_V4.bat');$s.WorkingDirectory=(Get-Location).Path;$s.IconLocation=(Join-Path (Get-Location).Path 'app_icon.ico,0');$s.Description='DUDC V4.0 - Cadastral Certificate Workflow Studio';$s.Save()" >nul 2>&1
)

cd /d "%~dp0DUDC V3"
call "Run_DUDC_V3.bat"
