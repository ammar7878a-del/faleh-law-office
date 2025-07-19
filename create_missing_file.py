#!/usr/bin/env python3
"""
إنشاء الملف المفقود للاختبار
"""

import os
from PIL import Image

# إنشاء الملف المفقود
upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
filename = "20250718_231048_اقامة_نعمان_قديمه.jpg"
file_path = os.path.join(upload_folder, filename)

print(f"🔧 إنشاء الملف المفقود: {filename}")
print(f"📁 المسار: {file_path}")

try:
    # إنشاء صورة تجريبية
    img = Image.new('RGB', (400, 300), color='lightblue')
    
    # إضافة نص للصورة
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    
    # استخدام خط افتراضي
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    # إضافة نص
    text = "اقامة نعمان قديمه"
    draw.text((50, 150), text, fill='black', font=font)
    draw.text((50, 180), "ملف تجريبي للاختبار", fill='black', font=font)
    
    # حفظ الصورة
    img.save(file_path, 'JPEG')
    
    print(f"✅ تم إنشاء الملف بنجاح")
    print(f"📏 حجم الملف: {os.path.getsize(file_path)} bytes")
    
except Exception as e:
    print(f"❌ خطأ في إنشاء الملف: {e}")
    
    # إنشاء ملف نصي بدلاً من الصورة
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("هذا ملف تجريبي لاختبار عرض المستندات\n")
            f.write("اسم الملف: اقامة نعمان قديمه\n")
            f.write("تم إنشاؤه للاختبار\n")
        
        print(f"✅ تم إنشاء ملف نصي بدلاً من الصورة")
        print(f"📏 حجم الملف: {os.path.getsize(file_path)} bytes")
        
    except Exception as e2:
        print(f"❌ خطأ في إنشاء الملف النصي: {e2}")

# التحقق من وجود الملف
if os.path.exists(file_path):
    print(f"✅ الملف موجود الآن: {file_path}")
else:
    print(f"❌ فشل في إنشاء الملف: {file_path}")
