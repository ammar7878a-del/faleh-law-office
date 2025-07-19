@echo off
echo ========================================
echo   مشاركة نظام ادارة المكتب القانوني
echo ========================================
echo.
echo الخطوة 1: تشغيل النظام...
echo.

REM تشغيل النظام في الخلفية
start /min "Law Office System" python final_working.py

REM انتظار تشغيل النظام
echo انتظار تشغيل النظام...
timeout /t 5 /nobreak >nul

echo.
echo الخطوة 2: تشغيل ngrok للمشاركة عبر الانترنت...
echo.
echo انتظر 10-15 ثانية حتى يظهر الرابط...
echo.

REM تشغيل ngrok
ngrok.exe http 3080

pause
