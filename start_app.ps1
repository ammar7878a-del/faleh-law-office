# PowerShell script to start the Law Office Management System

Write-Host "🏛️ المحامي فالح بن عقاب آل عيسى" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host "🚀 تشغيل التطبيق..." -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python غير مثبت أو غير موجود في PATH" -ForegroundColor Red
    Read-Host "اضغط Enter للخروج"
    exit 1
}

# Check required files
if (-not (Test-Path "app.py")) {
    Write-Host "❌ ملف app.py غير موجود" -ForegroundColor Red
    Read-Host "اضغط Enter للخروج"
    exit 1
}

if (-not (Test-Path "requirements.txt")) {
    Write-Host "❌ ملف requirements.txt غير موجود" -ForegroundColor Red
    Read-Host "اضغط Enter للخروج"
    exit 1
}

# Install requirements
Write-Host "📦 تثبيت المتطلبات..." -ForegroundColor Yellow
try {
    python -m pip install -r requirements.txt
    Write-Host "✅ تم تثبيت المتطلبات بنجاح" -ForegroundColor Green
} catch {
    Write-Host "❌ فشل في تثبيت المتطلبات" -ForegroundColor Red
    Read-Host "اضغط Enter للخروج"
    exit 1
}

# Create database if not exists
if (-not (Test-Path "instance\law_office.db")) {
    Write-Host "🗄️ إنشاء قاعدة البيانات..." -ForegroundColor Yellow
    try {
        python init_db.py
        Write-Host "✅ تم إنشاء قاعدة البيانات بنجاح" -ForegroundColor Green
    } catch {
        Write-Host "❌ فشل في إنشاء قاعدة البيانات" -ForegroundColor Red
        Read-Host "اضغط Enter للخروج"
        exit 1
    }
}

# Start the application
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "🌐 الرابط: http://localhost:5000" -ForegroundColor White
Write-Host "👤 مدير: admin / admin123" -ForegroundColor White
Write-Host "================================" -ForegroundColor Cyan
Write-Host "اضغط Ctrl+C لإيقاف التطبيق" -ForegroundColor Yellow
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

try {
    python app.py
} catch {
    Write-Host "❌ فشل في تشغيل التطبيق" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Read-Host "اضغط Enter للخروج"
