# دليل استكشاف الأخطاء - المحامي فالح بن عقاب آل عيسى

## 🚨 الأخطاء الشائعة وحلولها

### 1. خطأ: `TemplateAssertionError: block 'content' defined twice`

**السبب:** تكرار block content في ملف القالب

**الحل:**
```bash
# تم إصلاح هذا الخطأ في الإصدار الحالي
# تم إنشاء block منفصل للصفحات غير المصادق عليها (login_content)
```

### 1.1. خطأ: `TemplateNotFound: documents/index.html`

**السبب:** قوالب المستندات غير موجودة

**الحل:**
```bash
# تم إصلاح هذا الخطأ - تم إنشاء جميع القوالب المفقودة
# إذا ظهر خطأ مشابه، تأكد من وجود جميع ملفات القوالب
```

### 1.2. خطأ: `BuildError: Could not build url for endpoint 'auth.users'`

**السبب:** رابط غير موجود في المسارات

**الحل:**
```bash
# تم إصلاح هذا الخطأ - تم إنشاء route جديد لإدارة المستخدمين
# تم إضافة صفحة إدارة المستخدمين للمدير
```

### 2. خطأ: `ModuleNotFoundError: No module named 'flask'`

**السبب:** عدم تثبيت المتطلبات

**الحل:**
```bash
pip install -r requirements.txt
# أو
pip install flask flask-sqlalchemy flask-login flask-wtf flask-mail flask-migrate
```

### 3. خطأ: `cannot import name 'url_parse' from 'werkzeug.urls'`

**السبب:** إصدار werkzeug غير متوافق

**الحل:**
```bash
pip install werkzeug==2.3.7
# أو
pip install --upgrade werkzeug
```

### 4. خطأ: صفحة الويب لا تعمل

**الأسباب المحتملة:**
- التطبيق غير مشغل
- المنفذ 5000 مستخدم
- خطأ في الكود

**الحلول:**
```bash
# 1. تحقق من تشغيل التطبيق
python test_app.py

# 2. جرب منفذ آخر
python app.py  # ثم غير المنفذ في الكود

# 3. تحقق من الأخطاء
python -c "from app import create_app; app = create_app(); print('OK')"
```

### 5. خطأ: قاعدة البيانات

**الأعراض:**
- خطأ في إنشاء الجداول
- بيانات مفقودة
- خطأ في الاتصال

**الحلول:**
```bash
# إعادة إنشاء قاعدة البيانات
rm law_office.db
python test_app.py

# أو
python init_db.py
```

### 6. خطأ: تسجيل الدخول لا يعمل

**الأسباب:**
- كلمة مرور خاطئة
- المستخدم غير موجود
- المستخدم غير مفعل

**الحلول:**
```bash
# إنشاء مستخدم جديد
python test_app.py

# المستخدم الافتراضي:
# اسم المستخدم: admin
# كلمة المرور: admin123
```

### 7. خطأ: رفع الملفات لا يعمل

**السبب:** مجلد uploads غير موجود

**الحل:**
```bash
mkdir uploads
mkdir uploads/documents
mkdir uploads/avatars
```

### 8. خطأ: البريد الإلكتروني لا يعمل

**السبب:** إعدادات البريد غير صحيحة

**الحل:**
```bash
# تحديث ملف .env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

## 🔧 أدوات التشخيص

### فحص النظام
```bash
python test_app.py
```

### فحص المتطلبات
```bash
pip list | grep -i flask
```

### فحص قاعدة البيانات
```bash
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); print('Tables:', db.engine.table_names())"
```

### فحص المنافذ
```bash
# Windows
netstat -an | findstr :5000

# Linux/Mac
netstat -an | grep :5000
```

## 🚀 إعادة التشغيل الكامل

إذا واجهت مشاكل متعددة:

```bash
# 1. إيقاف التطبيق
# اضغط Ctrl+C

# 2. حذف قاعدة البيانات
rm law_office.db

# 3. إعادة تثبيت المتطلبات
pip uninstall flask flask-sqlalchemy flask-login flask-wtf flask-mail flask-migrate -y
pip install -r requirements.txt

# 4. إعادة إنشاء قاعدة البيانات
python test_app.py

# 5. تشغيل التطبيق
python app.py
```

## 📞 طلب المساعدة

### معلومات مطلوبة عند طلب المساعدة:

1. **نظام التشغيل:**
   ```bash
   # Windows
   systeminfo | findstr /B /C:"OS Name" /C:"OS Version"
   
   # Linux/Mac
   uname -a
   ```

2. **إصدار Python:**
   ```bash
   python --version
   ```

3. **رسالة الخطأ الكاملة:**
   ```bash
   # انسخ رسالة الخطأ كاملة من Terminal
   ```

4. **المتطلبات المثبتة:**
   ```bash
   pip list
   ```

## 🔍 سجلات الأخطاء

### عرض سجلات Flask:
```bash
# في Terminal حيث يعمل التطبيق
# ستظهر الأخطاء تلقائياً
```

### حفظ السجلات:
```bash
python app.py > app.log 2>&1
```

## ⚡ نصائح للأداء

### تحسين الأداء:
1. استخدم PostgreSQL بدلاً من SQLite للإنتاج
2. فعل التخزين المؤقت
3. ضغط الملفات الثابتة
4. استخدم CDN للمكتبات الخارجية

### مراقبة الأداء:
```bash
# مراقبة استخدام الذاكرة
python -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"

# مراقبة استخدام المعالج
python -c "import psutil; print(f'CPU: {psutil.cpu_percent()}%')"
```

## 🛡️ الأمان

### فحص الأمان:
1. تأكد من تغيير كلمة مرور المدير الافتراضية
2. استخدم HTTPS في الإنتاج
3. حدث المتطلبات بانتظام
4. فعل جدار الحماية

### النسخ الاحتياطي:
```bash
# نسخ احتياطي يدوي
cp law_office.db backup_$(date +%Y%m%d).db
cp -r uploads backup_uploads_$(date +%Y%m%d)
```

---

**إذا لم تجد حلاً لمشكلتك، راجع ملف README.md أو PROJECT_SUMMARY.md للمزيد من المعلومات.**
