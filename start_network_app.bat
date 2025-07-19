@echo off
chcp 65001 > nul
title نظام إدارة المكتب القانوني - الوصول من الشبكة
color 0A

echo ========================================
echo    نظام إدارة المكتب القانوني
echo    Law Office Management System
echo ========================================
echo.
echo    - إدارة العملاء والقضايا والمواعيد
echo    - Client, Case & Appointment Management
echo    - نظام الفواتير والمدفوعات
echo    - Invoice & Payment System
echo    - إدارة المستندات والملفات
echo    - Document & File Management
echo    - نظام الأدوار والصلاحيات
echo    - User Roles & Permissions System
echo    - 👑 مدير النظام - ⚖️ محامي - 📝 سكرتير
echo    - Admin - Lawyer - Secretary
echo    - نظام البحث المتقدم
echo    - Advanced Search System
echo    - 🔍 البحث برقم الهاتف والهوية واسم العميل
echo    - Search by Phone, ID, Client Name
echo    - واجهة مستخدم محسنة
echo    - Enhanced User Interface
echo    - 🎨 تصميم حديث وألوان متدرجة وتأثيرات بصرية
echo    - Modern Design, Gradients, Visual Effects
echo    - 🌐 الوصول من الشبكة المحلية
echo    - Network Access Available
echo.
echo ========================================

echo 🔧 جاري تشغيل النظام...
echo 🌐 سيكون متاحاً من الشبكة المحلية
echo.

echo ⚠️  تحذير أمني:
echo    النظام سيكون متاحاً لجميع الأجهزة في الشبكة المحلية
echo    تأكد من أن الشبكة آمنة وموثوقة
echo.

echo 🔥 إعدادات جدار الحماية:
echo    قد تحتاج لفتح البورت 8080 في جدار الحماية
echo    Windows Defender Firewall ^> Advanced Settings
echo    ^> Inbound Rules ^> New Rule ^> Port ^> TCP ^> 8080
echo.

pause

python final_working.py

echo.
echo ❌ تم إيقاف النظام
pause
