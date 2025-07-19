from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db
from app.cases import bp
from app.cases.forms import CaseForm, CaseSearchForm
from app.models import Case, Client, User, Appointment, Document, Invoice
from datetime import datetime, time

def combine_date_time(date_field, time_field):
    """دمج التاريخ والوقت في datetime واحد"""
    if not date_field:
        return None

    if time_field:
        try:
            # تحويل النص إلى وقت
            time_parts = time_field.split(':')
            if len(time_parts) == 2:
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                time_obj = time(hour, minute)
                return datetime.combine(date_field, time_obj)
        except (ValueError, IndexError):
            # إذا فشل تحويل الوقت، استخدم التاريخ فقط مع وقت افتراضي
            return datetime.combine(date_field, time(9, 0))  # 9:00 AM افتراضي

    # إذا لم يكن هناك وقت، استخدم 9:00 AM افتراضي
    return datetime.combine(date_field, time(9, 0))

@bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    case_type = request.args.get('case_type', '', type=str)
    status = request.args.get('status', '', type=str)
    
    query = Case.query
    
    # Apply filters
    if search:
        query = query.filter(
            db.or_(
                Case.title.contains(search),
                Case.case_number.contains(search),
                Case.description.contains(search)
            )
        )
    
    if case_type:
        query = query.filter(Case.case_type == case_type)
    
    if status:
        query = query.filter(Case.status == status)
    
    # If user is not admin, show only their cases
    if current_user.role != 'admin':
        query = query.filter(Case.lawyer_id == current_user.id)
    
    cases = query.order_by(Case.created_at.desc()).paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    
    next_url = url_for('cases.index', page=cases.next_num, search=search,
                      case_type=case_type, status=status) if cases.has_next else None
    prev_url = url_for('cases.index', page=cases.prev_num, search=search,
                      case_type=case_type, status=status) if cases.has_prev else None
    
    return render_template('cases/index.html', title='القضايا',
                         cases=cases.items, next_url=next_url, prev_url=prev_url,
                         search=search, case_type=case_type, status=status)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = CaseForm()
    if form.validate_on_submit():
        case = Case(
            case_number=form.case_number.data,
            title=form.title.data,
            description=form.description.data,
            case_type=form.case_type.data,
            status=form.status.data,
            priority=form.priority.data,
            client_id=form.client_id.data,
            lawyer_id=form.lawyer_id.data,
            court_name=form.court_name.data,
            judge_name=form.judge_name.data,
            opposing_party=form.opposing_party.data,
            opposing_lawyer=form.opposing_lawyer.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            next_hearing=combine_date_time(form.next_hearing_date.data, form.next_hearing_time.data)
        )
        db.session.add(case)
        db.session.commit()
        flash(f'تم إضافة القضية {case.case_number} بنجاح', 'success')
        return redirect(url_for('cases.view', id=case.id))
    
    return render_template('cases/form.html', title='إضافة قضية جديدة', form=form)

@bp.route('/<int:id>')
@login_required
def view(id):
    case = Case.query.get_or_404(id)
    
    # Check permissions
    if current_user.role != 'admin' and case.lawyer_id != current_user.id:
        flash('ليس لديك صلاحية لعرض هذه القضية', 'danger')
        return redirect(url_for('cases.index'))
    
    # Get case appointments
    appointments = Appointment.query.filter_by(case_id=id).order_by(
        Appointment.start_time.desc()).all()

    # Get case documents
    documents = Document.query.filter_by(case_id=id).order_by(
        Document.created_at.desc()).all()

    # Get case invoices
    invoices = Invoice.query.filter_by(case_id=id).order_by(
        Invoice.created_at.desc()).all()

    # Calculate counts
    appointments_count = len(appointments)
    documents_count = len(documents)
    invoices_count = len(invoices)

    return render_template('cases/view.html', title=f'القضية: {case.case_number}',
                         case=case, appointments=appointments, documents=documents,
                         invoices=invoices, appointments_count=appointments_count,
                         documents_count=documents_count, invoices_count=invoices_count,
                         today=datetime.now().date())

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    case = Case.query.get_or_404(id)
    
    # Check permissions
    if current_user.role != 'admin' and case.lawyer_id != current_user.id:
        flash('ليس لديك صلاحية لتعديل هذه القضية', 'danger')
        return redirect(url_for('cases.view', id=id))
    
    form = CaseForm(original_case_number=case.case_number)
    
    if form.validate_on_submit():
        case.case_number = form.case_number.data
        case.title = form.title.data
        case.description = form.description.data
        case.case_type = form.case_type.data
        case.status = form.status.data
        case.priority = form.priority.data
        case.client_id = form.client_id.data
        case.lawyer_id = form.lawyer_id.data
        case.court_name = form.court_name.data
        case.judge_name = form.judge_name.data
        case.opposing_party = form.opposing_party.data
        case.opposing_lawyer = form.opposing_lawyer.data
        case.start_date = form.start_date.data
        case.end_date = form.end_date.data
        case.next_hearing = combine_date_time(form.next_hearing_date.data, form.next_hearing_time.data)
        case.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash(f'تم تحديث القضية {case.case_number} بنجاح', 'success')
        return redirect(url_for('cases.view', id=case.id))
    
    elif request.method == 'GET':
        form.case_number.data = case.case_number
        form.title.data = case.title
        form.description.data = case.description
        form.case_type.data = case.case_type
        form.status.data = case.status
        form.priority.data = case.priority
        form.client_id.data = case.client_id
        form.lawyer_id.data = case.lawyer_id
        form.court_name.data = case.court_name
        form.judge_name.data = case.judge_name
        form.opposing_party.data = case.opposing_party
        form.opposing_lawyer.data = case.opposing_lawyer
        form.start_date.data = case.start_date
        form.end_date.data = case.end_date
        if case.next_hearing:
            form.next_hearing_date.data = case.next_hearing.date()
            form.next_hearing_time.data = case.next_hearing.strftime('%H:%M')
        else:
            form.next_hearing_date.data = None
            form.next_hearing_time.data = None
    
    return render_template('cases/form.html', title=f'تعديل القضية: {case.case_number}',
                         form=form, case=case)
