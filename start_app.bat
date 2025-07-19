@echo off
echo 🏛️ المحامي فالح بن عقاب آل عيسى
echo ================================
echo 🚀 تشغيل التطبيق...
echo.

REM تحقق من وجود Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python غير مثبت أو غير موجود في PATH
    pause
    exit /b 1
)

REM تحقق من وجود الملفات المطلوبة
if not exist "app.py" (
    echo ❌ ملف app.py غير موجود
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo ❌ ملف requirements.txt غير موجود
    pause
    exit /b 1
)

REM تثبيت المتطلبات
echo 📦 تثبيت المتطلبات...
python -m pip install -r requirements.txt

REM إنشاء قاعدة البيانات إذا لم تكن موجودة
if not exist "instance\law_office.db" (
    echo 🗄️ إنشاء قاعدة البيانات...
    python init_db.py
)

REM تشغيل التطبيق
echo.
echo ================================
echo 🌐 الرابط: http://localhost:5000
echo 👤 مدير: admin / admin123
echo ================================
echo اضغط Ctrl+C لإيقاف التطبيق
echo ================================
echo.

python app.py

pause
