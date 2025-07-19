#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اختبار دالة إنشاء أسماء الملفات الآمنة
"""

import re
from datetime import datetime

def safe_filename_with_timestamp(original_filename):
    """
    إنشاء اسم ملف آمن مع timestamp مع الحفاظ على الامتداد
    """
    if not original_filename:
        return None
    
    # فصل الاسم والامتداد
    if '.' in original_filename:
        name_part, extension = original_filename.rsplit('.', 1)
        extension = extension.lower()
    else:
        name_part = original_filename
        extension = ''
    
    # تنظيف اسم الملف (إزالة الأحرف الخطيرة)
    safe_name = re.sub(r'[^\w\s-]', '', name_part)
    safe_name = re.sub(r'[-\s]+', '_', safe_name)
    safe_name = safe_name.strip('_')
    
    # إذا كان الاسم فارغ بعد التنظيف، استخدم اسم افتراضي
    if not safe_name:
        safe_name = 'file'
    
    # إضافة timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # تجميع اسم الملف النهائي
    if extension:
        final_filename = f"{timestamp}_{safe_name}.{extension}"
    else:
        final_filename = f"{timestamp}_{safe_name}"
    
    return final_filename

def test_filename_function():
    """اختبار دالة إنشاء أسماء الملفات"""
    
    print("🧪 اختبار دالة إنشاء أسماء الملفات الآمنة")
    print("=" * 50)
    
    test_cases = [
        "الثلاجات.docx",
        "اقامة نعمان قديمه.jpg",
        "contract-2023.pdf",
        "ملف مهم.doc",
        "صورة العقد.png",
        "file with spaces.txt",
        "ملف@خطير#.xlsx",
        "simple.pdf",
        "no_extension",
        ".hidden",
        "file..with..dots.doc"
    ]
    
    for original in test_cases:
        safe = safe_filename_with_timestamp(original)
        print(f"الأصلي: {original}")
        print(f"الآمن:  {safe}")
        print("-" * 30)

if __name__ == '__main__':
    test_filename_function()
