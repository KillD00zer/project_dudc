@echo off
setlocal EnableExtensions
chcp 65001 > nul
title DUDC V3 - System Updater (GitHub)
cls
cd /d "%~dp0"

echo ======================================================================
echo   🏛️ DUDC V3 - أداة فحص وتحديث المنظومة من GitHub
echo ======================================================================
echo.

REM Verify Git
where git >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [خطأ] أداة Git غير مثبتة على هذا الحاسوب أو غير مضافة لـ PATH.
    echo للتحديث التلقائي يرجى تثبيت Git من: https://git-scm.com/
    echo.
    pause
    exit /b 1
)

echo [1/3] جارٍ الاتصال بمستودع GitHub وفحص التحديثات...
git fetch origin main >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [تحذير] تعذر الاتصال بمستودع GitHub. يرجى التحقق من اتصال الإنترنت.
    echo.
    pause
    exit /b 1
)

for /f %%a in ('git rev-parse --short HEAD') do set "LOCAL_HASH=%%a"
for /f %%a in ('git rev-parse --short origin/main') do set "REMOTE_HASH=%%a"

echo [2/3] الإصدار الحالي المثبت: [%LOCAL_HASH%]
echo       أحدث إصدار على GitHub: [%REMOTE_HASH%]
echo.

if "%LOCAL_HASH%"=="%REMOTE_HASH%" (
    echo ======================================================================
    echo   ✨ المنظومة محدثة بالكامل! أنت تعمل على أحدث كود رسمي.
    echo ======================================================================
    echo.
    pause
    exit /b 0
)

echo ======================================================================
echo   🚀 يوجد تحديث جديد متاح! تفاصيل ورسائل التحديث:
echo ======================================================================
echo.
git log HEAD..origin/main --pretty=format:"• %%s [%%h] (%%cr)%%n%%b"
echo.
echo ======================================================================
echo.

set /p CONFIRM="هل تريد سحب وتطبيق هذا التحديث الآن؟ (Y/N, الافتراضي Y): "
if /i "%CONFIRM%"=="N" (
    echo تم إلغاء عملية التحديث.
    pause
    exit /b 0
)

echo.
echo [3/3] جارٍ سحب التحديثات وتطبيقها (git pull)...
echo ----------------------------------------------------------------------
git pull origin main

if %ERRORLEVEL% neq 0 (
    echo.
    echo [تنبيه] وُجدت تعديلات محلية في ملفات الإعدادات. جارٍ تجاوزها تلقائياً واستكمال السحب...
    git stash >nul 2>&1
    git pull origin main
)

if %ERRORLEVEL% neq 0 (
    echo [تنبيه] محاولة ثانية لتطهير ملفات التتبع وسحب التحديث...
    git checkout -- . >nul 2>&1
    git pull origin main
)

if %ERRORLEVEL% equ 0 (
    echo.
    echo ======================================================================
    echo   ✔ تم تحديث المنظومة بنجاح إلى أحدث إصدار!
    echo ======================================================================
) else (
    echo.
    echo [خطأ] تعذر استكمال سحب التحديث. يرجى مراجعة رسائل الخطأ أعلاه.
)

echo.
pause
