from flask import render_template, request, current_app
from flask_login import login_required, current_user
from app.main import bp
from app.models import Case, Client, Appointment, Invoice
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    # Dashboard statistics
    total_cases = Case.query.count()
    active_cases = Case.query.filter_by(status='active').count()
    total_clients = Client.query.count()
    
    # Recent cases
    recent_cases = Case.query.order_by(Case.created_at.desc()).limit(5).all()
    
    # Upcoming appointments
    today = datetime.utcnow()
    upcoming_appointments = Appointment.query.filter(
        Appointment.start_time >= today,
        Appointment.status == 'scheduled'
    ).order_by(Appointment.start_time).limit(5).all()
    
    # Pending invoices
    pending_invoices = Invoice.query.filter_by(status='pending').count()
    overdue_invoices = Invoice.query.filter(
        Invoice.status == 'pending',
        Invoice.due_date < today.date()
    ).count()
    
    # Monthly revenue
    current_month = today.replace(day=1)
    monthly_revenue = db.session.query(func.sum(Invoice.total_amount)).filter(
        Invoice.status == 'paid',
        Invoice.paid_date >= current_month.date()
    ).scalar() or 0
    
    return render_template('main/index.html',
                         title='لوحة التحكم',
                         total_cases=total_cases,
                         active_cases=active_cases,
                         total_clients=total_clients,
                         recent_cases=recent_cases,
                         upcoming_appointments=upcoming_appointments,
                         pending_invoices=pending_invoices,
                         overdue_invoices=overdue_invoices,
                         monthly_revenue=monthly_revenue)

@bp.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    if not query:
        return render_template('main/search_results.html', 
                             title='البحث', 
                             query=query,
                             cases=[], 
                             clients=[])
    
    # Search in cases
    cases = Case.query.filter(
        db.or_(
            Case.title.contains(query),
            Case.case_number.contains(query),
            Case.description.contains(query)
        )
    ).all()
    
    # Search in clients
    clients = Client.query.filter(
        db.or_(
            Client.first_name.contains(query),
            Client.last_name.contains(query),
            Client.email.contains(query),
            Client.phone.contains(query)
        )
    ).all()
    
    return render_template('main/search_results.html',
                         title='نتائج البحث',
                         query=query,
                         cases=cases,
                         clients=clients)
