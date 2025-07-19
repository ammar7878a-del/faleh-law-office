from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired()])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])
    remember_me = BooleanField('تذكرني')
    submit = SubmitField('تسجيل الدخول')

class RegistrationForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    first_name = StringField('الاسم الأول', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('الاسم الأخير', validators=[DataRequired(), Length(max=64)])
    phone = StringField('رقم الهاتف', validators=[Length(max=20)])
    role = SelectField('الدور', choices=[
        ('lawyer', 'محامي'),
        ('secretary', 'سكرتير'),
        ('admin', 'مدير')
    ], default='lawyer')
    password = PasswordField('كلمة المرور', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('تأكيد كلمة المرور', 
                             validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('إنشاء حساب')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('اسم المستخدم مستخدم بالفعل. يرجى اختيار اسم آخر.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('البريد الإلكتروني مستخدم بالفعل. يرجى استخدام بريد آخر.')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('كلمة المرور الحالية', validators=[DataRequired()])
    new_password = PasswordField('كلمة المرور الجديدة', validators=[DataRequired(), Length(min=6)])
    new_password2 = PasswordField('تأكيد كلمة المرور الجديدة',
                                 validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('تغيير كلمة المرور')

class EditProfileForm(FlaskForm):
    first_name = StringField('الاسم الأول', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('الاسم الأخير', validators=[DataRequired(), Length(max=64)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    phone = StringField('رقم الهاتف', validators=[Length(max=20)])
    submit = SubmitField('حفظ التغييرات')
    
    def __init__(self, original_email, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_email = original_email
    
    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('البريد الإلكتروني مستخدم بالفعل. يرجى استخدام بريد آخر.')
