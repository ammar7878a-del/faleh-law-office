@echo off
chcp 65001 >nul
title نظام إدارة مكتب المحاماة - تشغيل آمن

echo ================================================================
echo 🏛️  نظام إدارة مكتب المحاماة
echo ⚖️  Law Office Management System  
echo ================================================================
echo.

echo 🔍 فحص إعدادات قاعدة البيانات...

REM فحص متغير قاعدة البيانات
if defined DATABASE_URL (
    echo ✅ تم العثور على قاعدة بيانات خارجية!
    echo 🔒 البيانات محفوظة دائماً - لن تُحذف أبداً!
    echo 🎉 مشكلة فقدان البيانات محلولة!
    set DATABASE_OK=1
) else (
    echo 🚨 تحذير: لا توجد قاعدة بيانات خارجية!
    echo ⚠️  البيانات ستُحذف عند إعادة التشغيل!
    echo 💥 هذا يعني أن جميع البيانات ستفقد!
    echo.
    echo 🔧 لحل هذه المشكلة:
    echo    1. راجع ملف QUICK_DATABASE_FIX.md
    echo    2. أنشئ قاعدة بيانات مجانية على Supabase
    echo    3. أضف متغير DATABASE_URL في إعدادات الخادم
    echo    4. أعد تشغيل التطبيق
    echo.
    echo 🔗 رابط Supabase: https://supabase.com
    echo 📖 دليل سريع: QUICK_DATABASE_FIX.md
    set DATABASE_OK=0
)

echo.
echo ================================================================

if %DATABASE_OK%==0 (
    echo 🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨
    echo تحذير مهم: البيانات ستُحذف عند إعادة التشغيل!
    echo لحل هذه المشكلة، راجع ملف: QUICK_DATABASE_FIX.md
    echo 🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨
    echo.
    set /p continue="هل تريد المتابعة رغم ذلك؟ (y/n): "
    if /i not "%continue%"=="y" if /i not "%continue%"=="yes" (
        echo تم إلغاء التشغيل.
        pause
        exit /b
    )
)

echo.
echo 🎯 التطبيق جاهز للتشغيل!
pause

echo.
echo 🚀 بدء تشغيل التطبيق...
echo ⏳ يرجى الانتظار...
echo.

REM تشغيل التطبيق
if exist "final_working.py" (
    python final_working.py
) else if exist "app.py" (
    python app.py
) else (
    echo ❌ ملف التطبيق غير موجود!
    echo تأكد من وجود final_working.py أو app.py
    pause
    exit /b 1
)

echo.
echo 🛑 تم إيقاف التطبيق
pause
