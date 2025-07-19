from datetime import datetime, timedelta
from app import db
from app.models import Appointment, Invoice
from app.email import send_appointment_reminder, send_invoice_notification

def send_appointment_reminders():
    """Send reminders for appointments in the next 24 hours"""
    tomorrow = datetime.utcnow() + timedelta(days=1)
    start_time = datetime.utcnow()
    end_time = tomorrow
    
    # Get appointments in the next 24 hours that haven't been reminded
    appointments = Appointment.query.filter(
        Appointment.start_time >= start_time,
        Appointment.start_time <= end_time,
        Appointment.status == 'scheduled',
        Appointment.reminder_sent == False
    ).all()
    
    for appointment in appointments:
        try:
            send_appointment_reminder(appointment)
            appointment.reminder_sent = True
            db.session.commit()
            print(f"Reminder sent for appointment: {appointment.title}")
        except Exception as e:
            print(f"Failed to send reminder for appointment {appointment.id}: {str(e)}")

def check_overdue_invoices():
    """Check for overdue invoices and update their status"""
    today = datetime.utcnow().date()
    
    # Find pending invoices that are past due date
    overdue_invoices = Invoice.query.filter(
        Invoice.status == 'pending',
        Invoice.due_date < today
    ).all()
    
    for invoice in overdue_invoices:
        invoice.status = 'overdue'
        db.session.commit()
        print(f"Invoice {invoice.invoice_number} marked as overdue")

def send_overdue_invoice_notifications():
    """Send notifications for overdue invoices"""
    overdue_invoices = Invoice.query.filter(
        Invoice.status == 'overdue'
    ).all()
    
    for invoice in overdue_invoices:
        try:
            # You can customize this to send overdue notifications
            # send_overdue_invoice_notification(invoice)
            print(f"Overdue invoice notification would be sent for: {invoice.invoice_number}")
        except Exception as e:
            print(f"Failed to send overdue notification for invoice {invoice.id}: {str(e)}")

def run_scheduled_tasks():
    """Run all scheduled tasks"""
    print("Running scheduled tasks...")
    
    try:
        send_appointment_reminders()
        check_overdue_invoices()
        send_overdue_invoice_notifications()
        print("Scheduled tasks completed successfully")
    except Exception as e:
        print(f"Error running scheduled tasks: {str(e)}")

if __name__ == '__main__':
    from app import create_app
    
    app = create_app()
    with app.app_context():
        run_scheduled_tasks()
