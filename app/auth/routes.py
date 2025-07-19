from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
try:
    from werkzeug.urls import url_parse
except ImportError:
    from urllib.parse import urlparse as url_parse
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, ChangePasswordForm, EditProfileForm
from app.models import User
from datetime import datetime

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('حسابك غير مفعل. يرجى الاتصال بالمدير.', 'warning')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        user.last_seen = datetime.utcnow()
        db.session.commit()
        
        next_page = request.args.get('next')
        try:
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('main.index')
        except:
            # Fallback for newer werkzeug versions
            from urllib.parse import urlparse
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('main.index')
        
        flash(f'مرحباً {user.full_name}!', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html', title='تسجيل الدخول', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    # Only admin can register new users
    if current_user.role != 'admin':
        flash('ليس لديك صلاحية لإنشاء مستخدمين جدد', 'danger')
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        flash(f'تم إنشاء حساب {user.full_name} بنجاح', 'success')
        return redirect(url_for('auth.users'))
    
    return render_template('auth/register.html', title='إنشاء مستخدم جديد', form=form)

@bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html', title='الملف الشخصي', user=current_user)

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.email)
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.email = form.email.data
        current_user.phone = form.phone.data
        db.session.commit()
        flash('تم حفظ التغييرات بنجاح', 'success')
        return redirect(url_for('auth.profile'))
    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.email.data = current_user.email
        form.phone.data = current_user.phone
    
    return render_template('auth/edit_profile.html', title='تعديل الملف الشخصي', form=form)

@bp.route('/users')
@login_required
def users():
    # Only admin can view users list
    if current_user.role != 'admin':
        flash('ليس لديك صلاحية لعرض قائمة المستخدمين', 'danger')
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)

    next_url = url_for('auth.users', page=users.next_num) if users.has_next else None
    prev_url = url_for('auth.users', page=users.prev_num) if users.has_prev else None

    return render_template('auth/users.html', title='إدارة المستخدمين',
                         users=users.items, next_url=next_url, prev_url=prev_url)

@bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    # Only admin can delete users
    if current_user.role != 'admin':
        flash('ليس لديك صلاحية لحذف المستخدمين', 'danger')
        return redirect(url_for('auth.users'))

    # Get the user to delete
    user_to_delete = User.query.get_or_404(user_id)

    # Prevent admin from deleting themselves
    if user_to_delete.id == current_user.id:
        flash('لا يمكنك حذف حسابك الخاص', 'danger')
        return redirect(url_for('auth.users'))

    # Check if user has associated cases
    if user_to_delete.cases.count() > 0:
        flash(f'لا يمكن حذف المستخدم {user_to_delete.full_name} لأنه مرتبط بقضايا موجودة', 'danger')
        return redirect(url_for('auth.users'))

    # Check if user has associated appointments
    if user_to_delete.appointments.count() > 0:
        flash(f'لا يمكن حذف المستخدم {user_to_delete.full_name} لأنه مرتبط بمواعيد موجودة', 'danger')
        return redirect(url_for('auth.users'))

    try:
        # Store user name for success message
        user_name = user_to_delete.full_name

        # Delete the user
        db.session.delete(user_to_delete)
        db.session.commit()

        flash(f'تم حذف المستخدم {user_name} بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash('حدث خطأ أثناء حذف المستخدم', 'danger')

    return redirect(url_for('auth.users'))

@bp.route('/test_delete')
@login_required
def test_delete():
    """صفحة اختبار وظيفة الحذف"""
    return render_template('test_delete.html', title='اختبار حذف المستخدمين')
