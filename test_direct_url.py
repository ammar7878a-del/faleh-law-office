#!/usr/bin/env python3
"""
اختبار مباشر للرابط المشكل
"""

from flask import Flask
import os
import urllib.parse

app = Flask(__name__)

# إعدادات الملفات
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/test_problematic_url')
def test_problematic_url():
    """اختبار الرابط المشكل"""
    
    # الرابط المشكل من الـ error
    problematic_filename = "20250719_181630_%D8%A7%D9%82%D8%A7%D9%85%D8%A9_%D9%86%D8%B9%D9%85%D8%A7%D9%86_%D9%82%D8%AF%D9%8A%D9%85%D9%87.jpg"
    
    # فك الترميز
    try:
        decoded = urllib.parse.unquote(problematic_filename, encoding='utf-8')
    except:
        decoded = "فشل في فك الترميز"
    
    # الملف الصحيح الموجود
    correct_filename = "20250718_231048_اقامة_نعمان_قديمه.jpg"
    
    return f'''
    <html dir="rtl">
    <head><title>تحليل المشكلة</title></head>
    <body style="font-family: Arial; padding: 20px;">
        <h2>🔍 تحليل مشكلة الملف</h2>
        
        <h3>الرابط المشكل:</h3>
        <p><strong>الأصلي:</strong> {problematic_filename}</p>
        <p><strong>بعد فك الترميز:</strong> {decoded}</p>
        
        <h3>الملف الصحيح الموجود:</h3>
        <p><strong>اسم الملف:</strong> {correct_filename}</p>
        
        <h3>المشكلة:</h3>
        <p>التاريخ والوقت مختلف:</p>
        <ul>
            <li><strong>المطلوب:</strong> 20250719_181630</li>
            <li><strong>الموجود:</strong> 20250718_231048</li>
        </ul>
        
        <h3>الحل:</h3>
        <p>يجب استخدام اسم الملف من قاعدة البيانات مباشرة، وليس إنشاء timestamp جديد</p>
        
        <hr>
        <h3>اختبار الإصلاح:</h3>
        <p><a href="/uploads/{correct_filename}" target="_blank">رابط الملف الصحيح</a></p>
        <p><a href="/uploads/{problematic_filename}" target="_blank">رابط الملف المشكل (سيتم إصلاحه)</a></p>
    </body>
    </html>
    '''

@app.route('/uploads/<path:filename>')
def serve_file(filename):
    """عرض الملفات مع الإصلاح"""
    try:
        print(f"🔍 طلب ملف: {filename}")
        
        # فك ترميز اسم الملف
        try:
            decoded_filename = urllib.parse.unquote(filename, encoding='utf-8')
            print(f"📝 بعد فك الترميز: {decoded_filename}")
        except Exception as e:
            print(f"❌ خطأ في فك الترميز: {e}")
            decoded_filename = filename
        
        # إصلاح المشكلة: إزالة أي مسارات خاطئة تحتوي على client/
        if 'client/' in filename:
            print(f"⚠️ تم اكتشاف 'client/' في الرابط: {filename}")
            clean_filename = filename.split('client/')[0].rstrip('_')
            print(f"🧹 اسم الملف بعد التنظيف: {clean_filename}")
            filename = clean_filename
        
        upload_folder = app.config['UPLOAD_FOLDER']
        
        # البحث عن الملف بأشكال مختلفة
        search_names = [filename, decoded_filename]
        
        # إضافة البحث بأسماء مشابهة (نفس النص، timestamps مختلفة)
        if '_' in decoded_filename:
            parts = decoded_filename.split('_', 2)  # تقسيم إلى تاريخ_وقت_اسم
            if len(parts) >= 3:
                name_part = parts[2]  # الجزء بعد التاريخ والوقت
                print(f"🔍 البحث عن ملفات تحتوي على: {name_part}")
                
                # البحث في جميع الملفات
                if os.path.exists(upload_folder):
                    for file in os.listdir(upload_folder):
                        if name_part in file and os.path.isfile(os.path.join(upload_folder, file)):
                            search_names.append(file)
                            print(f"✅ وجد ملف مشابه: {file}")
        
        print(f"🔍 أسماء البحث: {search_names}")
        
        file_path = None
        for search_name in search_names:
            test_path = os.path.join(upload_folder, search_name)
            print(f"🔍 فحص: {test_path}")
            if os.path.exists(test_path):
                file_path = test_path
                print(f"✅ الملف موجود: {test_path}")
                break
        
        if not file_path:
            print(f"❌ الملف غير موجود في جميع المسارات")
            return f"الملف غير موجود: {filename}", 404
        
        print(f"✅ تقديم الملف: {file_path}")
        from flask import send_from_directory
        return send_from_directory(upload_folder, os.path.basename(file_path))
        
    except Exception as e:
        print(f"❌ خطأ: {str(e)}")
        return f"خطأ: {str(e)}", 500

if __name__ == '__main__':
    print("🚀 بدء تشغيل اختبار الإصلاح...")
    print(f"📁 مجلد الرفع: {UPLOAD_FOLDER}")
    print("✅ التطبيق جاهز على http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
