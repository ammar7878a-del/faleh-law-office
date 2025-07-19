from flask import render_template, request, make_response, jsonify
from flask_login import login_required, current_user
from app import db
from app.reports import bp
from app.models import Case, Client, Invoice, Appointment, User
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from decimal import Decimal
import json

@bp.route('/')
@login_required
def index():
    return render_template('reports/index.html', title='التقارير')

@bp.route('/cases')
@login_required
def cases_report():
    # Get date range from request
    start_date = request.args.get('start_date', 
                                 (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # Convert to datetime objects
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    
    # Cases statistics
    total_cases = Case.query.filter(
        Case.created_at >= start_dt,
        Case.created_at < end_dt
    ).count()
    
    active_cases = Case.query.filter(
        Case.created_at >= start_dt,
        Case.created_at < end_dt,
        Case.status == 'active'
    ).count()
    
    closed_cases = Case.query.filter(
        Case.created_at >= start_dt,
        Case.created_at < end_dt,
        Case.status == 'closed'
    ).count()
    
    # Cases by type
    cases_by_type = db.session.query(
        Case.case_type,
        func.count(Case.id).label('count')
    ).filter(
        Case.created_at >= start_dt,
        Case.created_at < end_dt
    ).group_by(Case.case_type).all()
    
    # Cases by lawyer
    cases_by_lawyer = db.session.query(
        User.full_name,
        func.count(Case.id).label('count')
    ).join(Case, User.id == Case.lawyer_id).filter(
        Case.created_at >= start_dt,
        Case.created_at < end_dt
    ).group_by(User.id, User.first_name, User.last_name).all()
    
    # Monthly cases trend
    monthly_cases = db.session.query(
        extract('year', Case.created_at).label('year'),
        extract('month', Case.created_at).label('month'),
        func.count(Case.id).label('count')
    ).filter(
        Case.created_at >= start_dt,
        Case.created_at < end_dt
    ).group_by(
        extract('year', Case.created_at),
        extract('month', Case.created_at)
    ).order_by('year', 'month').all()
    
    return render_template('reports/cases.html', title='تقرير القضايا',
                         start_date=start_date, end_date=end_date,
                         total_cases=total_cases, active_cases=active_cases,
                         closed_cases=closed_cases, cases_by_type=cases_by_type,
                         cases_by_lawyer=cases_by_lawyer, monthly_cases=monthly_cases)

@bp.route('/financial')
@login_required
def financial_report():
    # Get date range from request
    start_date = request.args.get('start_date', 
                                 (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # Convert to datetime objects
    start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Financial statistics
    total_invoices = Invoice.query.filter(
        Invoice.issue_date >= start_dt,
        Invoice.issue_date <= end_dt
    ).count()
    
    total_revenue = db.session.query(func.sum(Invoice.total_amount)).filter(
        Invoice.issue_date >= start_dt,
        Invoice.issue_date <= end_dt,
        Invoice.status == 'paid'
    ).scalar() or Decimal('0.00')
    
    pending_amount = db.session.query(func.sum(Invoice.total_amount)).filter(
        Invoice.issue_date >= start_dt,
        Invoice.issue_date <= end_dt,
        Invoice.status == 'pending'
    ).scalar() or Decimal('0.00')
    
    overdue_amount = db.session.query(func.sum(Invoice.total_amount)).filter(
        Invoice.due_date < datetime.now().date(),
        Invoice.status == 'pending'
    ).scalar() or Decimal('0.00')
    
    # Revenue by month
    monthly_revenue = db.session.query(
        extract('year', Invoice.paid_date).label('year'),
        extract('month', Invoice.paid_date).label('month'),
        func.sum(Invoice.total_amount).label('revenue')
    ).filter(
        Invoice.paid_date >= start_dt,
        Invoice.paid_date <= end_dt,
        Invoice.status == 'paid'
    ).group_by(
        extract('year', Invoice.paid_date),
        extract('month', Invoice.paid_date)
    ).order_by('year', 'month').all()
    
    # Top clients by revenue
    top_clients = db.session.query(
        Client.first_name,
        Client.last_name,
        func.sum(Invoice.total_amount).label('total_revenue')
    ).join(Invoice, Client.id == Invoice.client_id).filter(
        Invoice.issue_date >= start_dt,
        Invoice.issue_date <= end_dt,
        Invoice.status == 'paid'
    ).group_by(Client.id, Client.first_name, Client.last_name).order_by(
        func.sum(Invoice.total_amount).desc()
    ).limit(10).all()
    
    return render_template('reports/financial.html', title='التقرير المالي',
                         start_date=start_date, end_date=end_date,
                         total_invoices=total_invoices, total_revenue=total_revenue,
                         pending_amount=pending_amount, overdue_amount=overdue_amount,
                         monthly_revenue=monthly_revenue, top_clients=top_clients)

@bp.route('/appointments')
@login_required
def appointments_report():
    # Get date range from request
    start_date = request.args.get('start_date', 
                                 (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # Convert to datetime objects
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
    
    # Appointments statistics
    total_appointments = Appointment.query.filter(
        Appointment.start_time >= start_dt,
        Appointment.start_time < end_dt
    ).count()
    
    completed_appointments = Appointment.query.filter(
        Appointment.start_time >= start_dt,
        Appointment.start_time < end_dt,
        Appointment.status == 'completed'
    ).count()
    
    cancelled_appointments = Appointment.query.filter(
        Appointment.start_time >= start_dt,
        Appointment.start_time < end_dt,
        Appointment.status == 'cancelled'
    ).count()
    
    # Appointments by type
    appointments_by_type = db.session.query(
        Appointment.appointment_type,
        func.count(Appointment.id).label('count')
    ).filter(
        Appointment.start_time >= start_dt,
        Appointment.start_time < end_dt
    ).group_by(Appointment.appointment_type).all()
    
    # Appointments by user
    appointments_by_user = db.session.query(
        User.first_name,
        User.last_name,
        func.count(Appointment.id).label('count')
    ).join(Appointment, User.id == Appointment.user_id).filter(
        Appointment.start_time >= start_dt,
        Appointment.start_time < end_dt
    ).group_by(User.id, User.first_name, User.last_name).all()
    
    return render_template('reports/appointments.html', title='تقرير المواعيد',
                         start_date=start_date, end_date=end_date,
                         total_appointments=total_appointments,
                         completed_appointments=completed_appointments,
                         cancelled_appointments=cancelled_appointments,
                         appointments_by_type=appointments_by_type,
                         appointments_by_user=appointments_by_user)

@bp.route('/export/<report_type>')
@login_required
def export_report(report_type):
    # This would implement Excel export functionality
    # For now, we'll return a simple CSV response
    
    if report_type == 'cases':
        # Export cases data
        cases = Case.query.all()
        csv_data = "رقم القضية,العنوان,العميل,المحامي,الحالة,تاريخ الإنشاء\n"
        for case in cases:
            csv_data += f"{case.case_number},{case.title},{case.client.full_name},{case.lawyer.full_name},{case.status},{case.created_at.strftime('%Y-%m-%d')}\n"
    
    elif report_type == 'financial':
        # Export financial data
        invoices = Invoice.query.all()
        csv_data = "رقم الفاتورة,العميل,المبلغ,الحالة,تاريخ الإصدار\n"
        for invoice in invoices:
            csv_data += f"{invoice.invoice_number},{invoice.client.full_name},{invoice.total_amount},{invoice.status},{invoice.issue_date}\n"
    
    else:
        csv_data = "نوع التقرير غير مدعوم\n"
    
    response = make_response(csv_data)
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename={report_type}_report.csv'
    
    return response
