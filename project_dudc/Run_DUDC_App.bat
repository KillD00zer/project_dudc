@echo off
chcp 65001 > nul
title Project DUDC - Cadastral Survey Certificate Generator
cls
echo ======================================================================
echo   Project DUDC - Cadastral Survey Certificate Generator
echo   Dakahlia Utility Data Center
echo.
echo   Starting application...
echo ======================================================================
start "" "%~dp0Certificate_Generator.exe"
