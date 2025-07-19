@echo off
echo ========================================
echo        تشغيل ngrok للمشاركة
echo ========================================
echo.
echo تأكد من تشغيل النظام أولاً!
echo.
echo سيظهر الرابط خلال 10-15 ثانية...
echo ابحث عن السطر الذي يحتوي على:
echo "Forwarding" و "https://xxxxx.ngrok.io"
echo.
echo اضغط Enter للمتابعة...
pause >nul

ngrok.exe http 3080
