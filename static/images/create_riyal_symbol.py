#!/usr/bin/env python3
from PIL import Image, ImageDraw
import os

# إنشاء مجلد الصور إذا لم يكن موجوداً
os.makedirs('static/images', exist_ok=True)

# إنشاء صورة جديدة
width, height = 24, 24
img = Image.new('RGBA', (width, height), (255, 255, 255, 0))  # خلفية شفافة
draw = ImageDraw.Draw(img)

# لون الرمز
color = (44, 62, 80, 255)  # #2c3e50

# رسم رمز الريال السعودي الجديد
# الخطوط العمودية
draw.rectangle([4, 2, 6, 18], fill=color)  # الخط العمودي الأيسر
draw.rectangle([10, 2, 12, 18], fill=color)  # الخط العمودي الأيمن

# الخطوط الأفقية
draw.rectangle([2, 6, 14, 8], fill=color)   # الخط الأفقي العلوي
draw.rectangle([2, 10, 14, 12], fill=color) # الخط الأفقي الأوسط
draw.rectangle([2, 14, 14, 16], fill=color) # الخط الأفقي السفلي

# الخطوط المائلة (تمثيل مبسط)
draw.rectangle([14, 6, 18, 8], fill=color)   # خط مائل علوي
draw.rectangle([16, 8, 20, 10], fill=color)  # خط مائل
draw.rectangle([14, 10, 18, 12], fill=color) # خط مائل أوسط
draw.rectangle([16, 12, 20, 14], fill=color) # خط مائل
draw.rectangle([14, 14, 18, 16], fill=color) # خط مائل سفلي

# حفظ الصورة
img.save('static/images/riyal_symbol.png', 'PNG')
print("تم إنشاء رمز الريال السعودي بنجاح!")
