@echo off
chcp 65001 > nul
title نظام إدارة المكتب القانوني - الوصول عبر الإنترنت
color 0A

echo ========================================
echo    نظام إدارة المكتب القانوني
echo    الوصول عبر الإنترنت باستخدام ngrok
echo ========================================
echo.
echo 🌐 هذا الملف يتيح الوصول للنظام من أي مكان في العالم
echo ⚠️  تحذير: النظام سيكون متاحاً عبر الإنترنت
echo.

echo 📋 المتطلبات:
echo    1. تحميل ngrok من: https://ngrok.com/
echo    2. إنشاء حساب مجاني
echo    3. وضع ngrok.exe في نفس مجلد النظام
echo.

echo 🔍 فحص وجود ngrok...
if not exist "ngrok.exe" (
    echo ❌ ngrok.exe غير موجود!
    echo.
    echo 📥 يرجى تحميل ngrok من: https://ngrok.com/download
    echo 📁 ووضع ngrok.exe في المجلد: %cd%
    echo.
    pause
    exit /b 1
)

echo ✅ تم العثور على ngrok
echo.

echo 🚀 جاري تشغيل النظام...
start "Law Office System" python final_working.py

echo ⏳ انتظار تشغيل النظام...
timeout /t 5 /nobreak > nul

echo 🌐 جاري إنشاء نفق ngrok...
echo.
echo 📋 معلومات مهمة:
echo    - سيتم إنشاء رابط مؤقت للوصول عبر الإنترنت
echo    - الرابط صالح طالما البرنامج يعمل
echo    - أغلق هذه النافذة لإيقاف الوصول عبر الإنترنت
echo.

ngrok http 8080

echo.
echo ❌ تم إيقاف ngrok
echo 🔒 النظام لم يعد متاحاً عبر الإنترنت
pause
