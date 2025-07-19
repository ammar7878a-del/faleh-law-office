from flask import current_app, render_template
from flask_mail import Message
from app import mail
import threading

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    
    # Send email asynchronously
    thread = threading.Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    )
    thread.start()

def send_appointment_reminder(appointment):
    """Send appointment reminder email"""
    if not appointment.case or not appointment.case.client.email:
        return
    
    subject = f"تذكير بموعد: {appointment.title}"
    sender = current_app.config['MAIL_USERNAME']
    recipients = [appointment.case.client.email]
    
    text_body = f"""
    عزيزي {appointment.case.client.full_name},
    
    نذكركم بموعدكم القادم:
    
    العنوان: {appointment.title}
    التاريخ والوقت: {appointment.start_time.strftime('%Y-%m-%d %H:%M')}
    المكان: {appointment.location or 'غير محدد'}
    
    مع تحيات مكتب المحاماة
    """
    
    html_body = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif;">
        <h2>تذكير بموعد</h2>
        <p>عزيزي {appointment.case.client.full_name},</p>
        <p>نذكركم بموعدكم القادم:</p>
        <ul>
            <li><strong>العنوان:</strong> {appointment.title}</li>
            <li><strong>التاريخ والوقت:</strong> {appointment.start_time.strftime('%Y-%m-%d %H:%M')}</li>
            <li><strong>المكان:</strong> {appointment.location or 'غير محدد'}</li>
        </ul>
        <p>مع تحيات مكتب المحاماة</p>
    </div>
    """
    
    send_email(subject, sender, recipients, text_body, html_body)

def send_invoice_notification(invoice):
    """Send invoice notification email"""
    if not invoice.client.email:
        return
    
    subject = f"فاتورة جديدة رقم: {invoice.invoice_number}"
    sender = current_app.config['MAIL_USERNAME']
    recipients = [invoice.client.email]
    
    text_body = f"""
    عزيزي {invoice.client.full_name},
    
    تم إصدار فاتورة جديدة لكم:
    
    رقم الفاتورة: {invoice.invoice_number}
    المبلغ الإجمالي: {invoice.total_amount} ر.س
    تاريخ الاستحقاق: {invoice.due_date}
    
    يرجى سداد المبلغ في الموعد المحدد.
    
    مع تحيات مكتب المحاماة
    """
    
    html_body = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif;">
        <h2>فاتورة جديدة</h2>
        <p>عزيزي {invoice.client.full_name},</p>
        <p>تم إصدار فاتورة جديدة لكم:</p>
        <ul>
            <li><strong>رقم الفاتورة:</strong> {invoice.invoice_number}</li>
            <li><strong>المبلغ الإجمالي:</strong> {invoice.total_amount} ر.س</li>
            <li><strong>تاريخ الاستحقاق:</strong> {invoice.due_date}</li>
        </ul>
        <p>يرجى سداد المبلغ في الموعد المحدد.</p>
        <p>مع تحيات مكتب المحاماة</p>
    </div>
    """
    
    send_email(subject, sender, recipients, text_body, html_body)

def send_case_update_notification(case, update_message):
    """Send case update notification email"""
    if not case.client.email:
        return
    
    subject = f"تحديث على القضية: {case.case_number}"
    sender = current_app.config['MAIL_USERNAME']
    recipients = [case.client.email]
    
    text_body = f"""
    عزيزي {case.client.full_name},
    
    يوجد تحديث على قضيتكم:
    
    رقم القضية: {case.case_number}
    عنوان القضية: {case.title}
    
    التحديث:
    {update_message}
    
    مع تحيات مكتب المحاماة
    """
    
    html_body = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif;">
        <h2>تحديث على القضية</h2>
        <p>عزيزي {case.client.full_name},</p>
        <p>يوجد تحديث على قضيتكم:</p>
        <ul>
            <li><strong>رقم القضية:</strong> {case.case_number}</li>
            <li><strong>عنوان القضية:</strong> {case.title}</li>
        </ul>
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
            <strong>التحديث:</strong><br>
            {update_message}
        </div>
        <p>مع تحيات مكتب المحاماة</p>
    </div>
    """
    
    send_email(subject, sender, recipients, text_body, html_body)
