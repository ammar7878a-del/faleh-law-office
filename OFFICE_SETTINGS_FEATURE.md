# ميزة إعدادات المكتب - Office Settings Feature

## 🎉 تم إضافة صفحة إعدادات المكتب بنجاح!

---

## 🆕 الميزة الجديدة

### **📋 وصف الميزة:**
صفحة شاملة لإدارة وتحديث جميع بيانات المكتب والمعلومات الأساسية، مما يتيح للمدير تخصيص النظام بالكامل حسب بيانات مكتبه.

### **🎯 الهدف:**
- تخصيص النظام ليعكس هوية المكتب
- إدارة مركزية لجميع بيانات المكتب
- سهولة تحديث المعلومات دون الحاجة لتعديل الكود
- عرض بيانات المكتب في جميع الصفحات والتقارير

---

## 🗃️ نموذج قاعدة البيانات

### **جدول OfficeSettings:**
```sql
CREATE TABLE office_settings (
    id INTEGER PRIMARY KEY,
    office_name VARCHAR(200) NOT NULL DEFAULT 'مكتب المحاماة',
    office_name_en VARCHAR(200) DEFAULT 'Law Office',
    address TEXT,
    city VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100) DEFAULT 'المملكة العربية السعودية',
    
    -- معلومات التسجيل
    commercial_register VARCHAR(50),  -- السجل التجاري
    tax_number VARCHAR(50),          -- الرقم الضريبي
    license_number VARCHAR(50),      -- رقم الترخيص
    
    -- معلومات الاتصال
    phone_1 VARCHAR(20),             -- الهاتف الأساسي
    phone_2 VARCHAR(20),             -- هاتف إضافي
    fax VARCHAR(20),                 -- الفاكس
    email VARCHAR(120),              -- البريد الإلكتروني
    website VARCHAR(200),            -- الموقع الإلكتروني
    
    -- معلومات إضافية
    logo_path VARCHAR(200),          -- مسار الشعار
    established_year INTEGER,        -- سنة التأسيس
    description TEXT,                -- وصف المكتب
    
    -- إعدادات النظام
    currency VARCHAR(10) DEFAULT 'ريال',
    language VARCHAR(10) DEFAULT 'ar',
    timezone VARCHAR(50) DEFAULT 'Asia/Riyadh',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### **الوظائف المضافة:**
```python
@staticmethod
def get_settings():
    """الحصول على إعدادات المكتب أو إنشاء إعدادات افتراضية"""
    settings = OfficeSettings.query.first()
    if not settings:
        settings = OfficeSettings(
            office_name='مكتب المحاماة',
            office_name_en='Law Office',
            country='المملكة العربية السعودية',
            currency='ريال',
            language='ar',
            timezone='Asia/Riyadh'
        )
        db.session.add(settings)
        db.session.commit()
    return settings
```

---

## 🎨 واجهة المستخدم

### **🎯 تصميم الصفحة:**

#### **1. Header Card:**
- تصميم متدرج جذاب (أزرق إلى بنفسجي)
- أيقونة إعدادات كبيرة
- عنوان واضح ووصف للصفحة

#### **2. أقسام النموذج:**

##### **📋 معلومات المكتب الأساسية:**
- اسم المكتب (عربي) *
- اسم المكتب (إنجليزي)
- سنة التأسيس
- العملة (قائمة منسدلة)
- وصف المكتب

##### **🏠 العنوان ومعلومات الموقع:**
- العنوان التفصيلي
- المدينة
- الرمز البريدي
- الدولة

##### **📜 معلومات التسجيل والترخيص:**
- السجل التجاري
- الرقم الضريبي
- رقم الترخيص

##### **📞 معلومات الاتصال:**
- الهاتف الأساسي
- هاتف إضافي
- الفاكس
- البريد الإلكتروني
- الموقع الإلكتروني

#### **3. تصميم متجاوب:**
- يعمل على جميع أحجام الشاشات
- تخطيط مرن للحقول
- أزرار كبيرة وواضحة

### **🎨 التصميم المرئي:**
```css
.settings-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 15px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}

.form-section {
    background: white;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}

.btn-save {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    border-radius: 25px;
    padding: 12px 30px;
    color: white;
    font-weight: bold;
    transition: all 0.3s ease;
}
```

---

## 🔧 الوظائف المضافة

### **1. صفحة عرض الإعدادات:**
```python
@app.route('/office_settings')
@login_required
@admin_required
def office_settings():
    """صفحة إعدادات المكتب"""
    settings = OfficeSettings.get_settings()
    return render_template_string(...)
```

### **2. تحديث الإعدادات:**
```python
@app.route('/office_settings', methods=['POST'])
@login_required
@admin_required
def update_office_settings():
    """تحديث إعدادات المكتب"""
    try:
        settings = OfficeSettings.get_settings()
        
        # تحديث جميع البيانات
        settings.office_name = request.form.get('office_name', '').strip()
        settings.office_name_en = request.form.get('office_name_en', '').strip()
        # ... باقي الحقول
        
        settings.updated_at = datetime.utcnow()
        db.session.commit()
        flash('تم حفظ إعدادات المكتب بنجاح', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حفظ الإعدادات: {str(e)}', 'error')
    
    return redirect(url_for('office_settings'))
```

### **3. إنشاء إعدادات افتراضية:**
```python
# في بداية التطبيق
if OfficeSettings.query.count() == 0:
    default_settings = OfficeSettings(
        office_name='مكتب فالح آل عيسى للمحاماة',
        office_name_en='Faleh Al-Issa Law Office',
        address='الرياض، المملكة العربية السعودية',
        city='الرياض',
        country='المملكة العربية السعودية',
        currency='ريال',
        language='ar',
        timezone='Asia/Riyadh',
        description='مكتب محاماة متخصص في جميع الخدمات القانونية'
    )
    db.session.add(default_settings)
    db.session.commit()
```

---

## 🔗 التكامل مع النظام

### **1. إضافة رابط في لوحة التحكم:**
```html
{% if current_user.role == 'admin' %}
<div class="col-lg-3 col-md-6 mb-3">
    <a href="/office_settings" class="btn btn-info btn-lg w-100">
        <i class="fas fa-cogs me-2"></i>
        <div>
            <strong>إعدادات المكتب</strong>
            <small class="d-block">بيانات المكتب</small>
        </div>
    </a>
</div>
{% endif %}
```

### **2. استخدام اسم المكتب في جميع الصفحات:**
```python
# في كل دالة عرض
office_settings = OfficeSettings.get_settings()

# في القوالب
<title>{{ office_settings.office_name }} - نظام إدارة المكتب القانوني</title>
<a class="navbar-brand" href="/">
    <i class="fas fa-balance-scale me-2"></i>
    {{ office_settings.office_name }}
</a>
```

### **3. استخدام البيانات في التقارير:**
- اسم المكتب في رأس الفواتير
- عنوان المكتب في المراسلات
- أرقام الهواتف في جهات الاتصال
- السجل التجاري والرقم الضريبي في الوثائق الرسمية

---

## 🛡️ الأمان والصلاحيات

### **🔒 قيود الوصول:**
- **المدير فقط:** يمكنه الوصول لصفحة الإعدادات
- **محمي بتسجيل الدخول:** `@login_required`
- **محمي بصلاحية المدير:** `@admin_required`

### **✅ التحقق من البيانات:**
- التحقق من وجود اسم المكتب (مطلوب)
- تنظيف البيانات المدخلة (`strip()`)
- معالجة الأخطاء مع `try/except`
- إرجاع قاعدة البيانات عند الخطأ (`rollback()`)

### **📝 رسائل المستخدم:**
- رسالة نجاح عند الحفظ
- رسائل خطأ واضحة عند المشاكل
- تأكيدات بصرية للعمليات

---

## 🎯 الميزات المتقدمة

### **1. العملات المدعومة:**
- ريال سعودي
- درهم إماراتي
- دينار كويتي
- دولار أمريكي

### **2. التحديث التلقائي:**
- تحديث `updated_at` عند كل تعديل
- حفظ تاريخ الإنشاء `created_at`

### **3. البيانات الافتراضية:**
- إنشاء تلقائي للإعدادات عند أول تشغيل
- قيم افتراضية منطقية
- دعم اللغة العربية

### **4. التصميم التفاعلي:**
- تأثيرات hover على الأزرار
- تدرجات لونية جذابة
- أيقونات واضحة لكل قسم
- تخطيط منظم ومرتب

---

## 📊 الاستخدام العملي

### **🎯 للمكاتب الجديدة:**
1. تسجيل الدخول كمدير
2. الذهاب لإعدادات المكتب
3. إدخال جميع بيانات المكتب
4. حفظ الإعدادات
5. ستظهر البيانات في جميع أنحاء النظام

### **🔄 للمكاتب الموجودة:**
1. تحديث البيانات حسب الحاجة
2. إضافة معلومات جديدة
3. تعديل أرقام الهواتف أو العناوين
4. تحديث السجلات الرسمية

### **📋 في التقارير والفواتير:**
- اسم المكتب يظهر تلقائياً
- العنوان في المراسلات
- أرقام التواصل في جهات الاتصال
- السجل التجاري في الوثائق

---

## 🚀 الخطوات التالية المقترحة

### **1. تحسينات مستقبلية:**
- إضافة رفع شعار المكتب
- دعم عدة لغات
- إعدادات ألوان النظام
- قوالب مخصصة للفواتير

### **2. ميزات إضافية:**
- نسخ احتياطي للإعدادات
- استيراد/تصدير الإعدادات
- سجل تغييرات الإعدادات
- إعدادات البريد الإلكتروني

---

## ✅ النتيجة النهائية

### 🎉 **تم إضافة صفحة إعدادات المكتب بنجاح!**

✅ **نموذج قاعدة بيانات شامل للإعدادات**  
✅ **واجهة مستخدم جذابة ومنظمة**  
✅ **تكامل كامل مع النظام الموجود**  
✅ **أمان وصلاحيات محكمة**  
✅ **إعدادات افتراضية ذكية**  
✅ **تصميم متجاوب لجميع الأجهزة**  
✅ **رسائل مستخدم واضحة**  
✅ **معالجة أخطاء شاملة**  

النظام الآن يدعم تخصيص كامل لبيانات المكتب! 🏢✨

---

**تاريخ الإضافة**: 2025-07-14  
**الحالة**: مكتمل ومُختبر ✅  
**المطور**: Augment Agent

---

## 🎯 للوصول للميزة

1. **تسجيل الدخول كمدير**
2. **الذهاب للوحة التحكم**
3. **الضغط على "إعدادات المكتب"**
4. **تعديل البيانات وحفظها**

الرابط المباشر: http://127.0.0.1:8080/office_settings 🚀
