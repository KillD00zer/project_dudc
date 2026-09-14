@echo off
chcp 65001 > nul
title Cadastral Survey Certificate Generator
cls
echo ======================================================================
echo   Cadastral Survey Certificate Generator
echo   Starting local server and opening web interface...
echo ======================================================================
echo.
python "%~dp0app_server.py"
pause
