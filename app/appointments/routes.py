from flask import render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from app.appointments import bp
from app.appointments.forms import AppointmentForm, AppointmentSearchForm
from app.models import Appointment, Case, Client
from datetime import datetime, timedelta

@bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    appointment_type = request.args.get('appointment_type', '', type=str)
    status = request.args.get('status', '', type=str)
    
    query = Appointment.query
    
    # Apply filters
    if search:
        query = query.filter(
            db.or_(
                Appointment.title.contains(search),
                Appointment.description.contains(search),
                Appointment.location.contains(search)
            )
        )
    
    if appointment_type:
        query = query.filter(Appointment.appointment_type == appointment_type)
    
    if status:
        query = query.filter(Appointment.status == status)
    
    # If user is not admin, show only their appointments
    if current_user.role != 'admin':
        query = query.filter(Appointment.user_id == current_user.id)
    
    appointments = query.order_by(Appointment.start_time.desc()).paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    
    next_url = url_for('appointments.index', page=appointments.next_num, 
                      search=search, appointment_type=appointment_type, 
                      status=status) if appointments.has_next else None
    prev_url = url_for('appointments.index', page=appointments.prev_num,
                      search=search, appointment_type=appointment_type,
                      status=status) if appointments.has_prev else None
    
    return render_template('appointments/index.html', title='المواعيد',
                         appointments=appointments.items, next_url=next_url, 
                         prev_url=prev_url, search=search, 
                         appointment_type=appointment_type, status=status)

@bp.route('/calendar')
@login_required
def calendar():
    return render_template('appointments/calendar.html', title='التقويم')

@bp.route('/api/events')
@login_required
def api_events():
    start = request.args.get('start')
    end = request.args.get('end')
    
    query = Appointment.query
    
    if start and end:
        start_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(end.replace('Z', '+00:00'))
        query = query.filter(
            Appointment.start_time >= start_date,
            Appointment.start_time <= end_date
        )
    
    # If user is not admin, show only their appointments
    if current_user.role != 'admin':
        query = query.filter(Appointment.user_id == current_user.id)
    
    appointments = query.all()
    
    events = []
    for appointment in appointments:
        color = {
            'hearing': '#dc3545',  # red
            'meeting': '#007bff',  # blue
            'consultation': '#28a745',  # green
            'other': '#6c757d'  # gray
        }.get(appointment.appointment_type, '#6c757d')
        
        events.append({
            'id': appointment.id,
            'title': appointment.title,
            'start': appointment.start_time.isoformat(),
            'end': appointment.end_time.isoformat(),
            'backgroundColor': color,
            'borderColor': color,
            'url': url_for('appointments.view', id=appointment.id)
        })
    
    return jsonify(events)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = AppointmentForm()
    if form.validate_on_submit():
        appointment = Appointment(
            title=form.title.data,
            description=form.description.data,
            appointment_type=form.appointment_type.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            location=form.location.data,
            status=form.status.data,
            case_id=form.case_id.data if form.case_id.data != 0 else None,
            client_id=form.client_id.data if form.client_id.data != 0 else None,
            notes=form.notes.data,
            user_id=current_user.id
        )
        db.session.add(appointment)
        db.session.commit()
        flash(f'تم إضافة الموعد "{appointment.title}" بنجاح', 'success')
        return redirect(url_for('appointments.view', id=appointment.id))
    
    return render_template('appointments/form.html', title='إضافة موعد جديد', form=form)

@bp.route('/<int:id>')
@login_required
def view(id):
    appointment = Appointment.query.get_or_404(id)
    
    # Check permissions
    if current_user.role != 'admin' and appointment.user_id != current_user.id:
        flash('ليس لديك صلاحية لعرض هذا الموعد', 'danger')
        return redirect(url_for('appointments.index'))
    
    return render_template('appointments/view.html', 
                         title=f'الموعد: {appointment.title}',
                         appointment=appointment)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    appointment = Appointment.query.get_or_404(id)
    
    # Check permissions
    if current_user.role != 'admin' and appointment.user_id != current_user.id:
        flash('ليس لديك صلاحية لتعديل هذا الموعد', 'danger')
        return redirect(url_for('appointments.view', id=id))
    
    form = AppointmentForm()
    
    if form.validate_on_submit():
        appointment.title = form.title.data
        appointment.description = form.description.data
        appointment.appointment_type = form.appointment_type.data
        appointment.start_time = form.start_time.data
        appointment.end_time = form.end_time.data
        appointment.location = form.location.data
        appointment.status = form.status.data
        appointment.case_id = form.case_id.data if form.case_id.data != 0 else None
        appointment.client_id = form.client_id.data if form.client_id.data != 0 else None
        appointment.notes = form.notes.data
        
        db.session.commit()
        flash(f'تم تحديث الموعد "{appointment.title}" بنجاح', 'success')
        return redirect(url_for('appointments.view', id=appointment.id))
    
    elif request.method == 'GET':
        form.title.data = appointment.title
        form.description.data = appointment.description
        form.appointment_type.data = appointment.appointment_type
        form.start_time.data = appointment.start_time
        form.end_time.data = appointment.end_time
        form.location.data = appointment.location
        form.status.data = appointment.status
        form.case_id.data = appointment.case_id or 0
        form.client_id.data = appointment.client_id or 0
        form.notes.data = appointment.notes
    
    return render_template('appointments/form.html', 
                         title=f'تعديل الموعد: {appointment.title}',
                         form=form, appointment=appointment)
