from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db
from app.clients import bp
from app.clients.forms import ClientForm, ClientSearchForm
from app.models import Client, Case
from datetime import datetime

@bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = Client.query
    if search:
        query = query.filter(
            db.or_(
                Client.first_name.contains(search),
                Client.last_name.contains(search),
                Client.email.contains(search),
                Client.phone.contains(search),
                Client.mobile.contains(search),
                Client.national_id.contains(search)
            )
        )
    
    clients = query.order_by(Client.created_at.desc()).paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    
    next_url = url_for('clients.index', page=clients.next_num, search=search) \
        if clients.has_next else None
    prev_url = url_for('clients.index', page=clients.prev_num, search=search) \
        if clients.has_prev else None
    
    return render_template('clients/index.html', title='العملاء',
                         clients=clients.items, next_url=next_url,
                         prev_url=prev_url, search=search)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = ClientForm()
    if form.validate_on_submit():
        client = Client(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone=form.phone.data,
            mobile=form.mobile.data,
            address=form.address.data,
            national_id=form.national_id.data,
            company=form.company.data,
            notes=form.notes.data
        )
        db.session.add(client)
        db.session.commit()
        flash(f'تم إضافة العميل {client.full_name} بنجاح', 'success')
        return redirect(url_for('clients.view', id=client.id))
    
    return render_template('clients/form.html', title='إضافة عميل جديد', form=form)

@bp.route('/<int:id>')
@login_required
def view(id):
    client = Client.query.get_or_404(id)
    
    # Get client's cases
    cases = Case.query.filter_by(client_id=id).order_by(Case.created_at.desc()).all()
    
    return render_template('clients/view.html', title=f'العميل: {client.full_name}',
                         client=client, cases=cases)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    client = Client.query.get_or_404(id)
    form = ClientForm(original_national_id=client.national_id)
    
    if form.validate_on_submit():
        client.first_name = form.first_name.data
        client.last_name = form.last_name.data
        client.email = form.email.data
        client.phone = form.phone.data
        client.mobile = form.mobile.data
        client.address = form.address.data
        client.national_id = form.national_id.data
        client.company = form.company.data
        client.notes = form.notes.data
        client.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash(f'تم تحديث بيانات العميل {client.full_name} بنجاح', 'success')
        return redirect(url_for('clients.view', id=client.id))
    
    elif request.method == 'GET':
        form.first_name.data = client.first_name
        form.last_name.data = client.last_name
        form.email.data = client.email
        form.phone.data = client.phone
        form.mobile.data = client.mobile
        form.address.data = client.address
        form.national_id.data = client.national_id
        form.company.data = client.company
        form.notes.data = client.notes
    
    return render_template('clients/form.html', title=f'تعديل العميل: {client.full_name}',
                         form=form, client=client)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    client = Client.query.get_or_404(id)
    
    # Check if client has cases
    if client.cases.count() > 0:
        flash('لا يمكن حذف العميل لأنه مرتبط بقضايا', 'danger')
        return redirect(url_for('clients.view', id=id))
    
    client_name = client.full_name
    db.session.delete(client)
    db.session.commit()
    flash(f'تم حذف العميل {client_name} بنجاح', 'success')
    return redirect(url_for('clients.index'))
