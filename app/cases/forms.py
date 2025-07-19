from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, ValidationError
from app.models import Case, Client, User
from datetime import datetime

class CaseForm(FlaskForm):
    case_number = StringField('رقم القضية', validators=[DataRequired(), Length(max=50)])
    title = StringField('عنوان القضية', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('وصف القضية', validators=[Optional()])
    case_type = SelectField('نوع القضية', choices=[
        ('civil', 'مدنية'),
        ('criminal', 'جنائية'),
        ('commercial', 'تجارية'),
        ('administrative', 'إدارية'),
        ('labor', 'عمالية'),
        ('family', 'أحوال شخصية'),
        ('real_estate', 'عقارية'),
        ('other', 'أخرى')
    ], validators=[DataRequired()])
    status = SelectField('حالة القضية', choices=[
        ('active', 'نشطة'),
        ('closed', 'مغلقة'),
        ('suspended', 'معلقة')
    ], default='active')
    priority = SelectField('الأولوية', choices=[
        ('low', 'منخفضة'),
        ('medium', 'متوسطة'),
        ('high', 'عالية')
    ], default='medium')
    client_id = SelectField('العميل', coerce=int, validators=[DataRequired()])
    lawyer_id = SelectField('المحامي المسؤول', coerce=int, validators=[DataRequired()])
    court_name = StringField('اسم المحكمة', validators=[Optional(), Length(max=100)])
    judge_name = StringField('اسم القاضي', validators=[Optional(), Length(max=100)])
    opposing_party = StringField('الطرف المقابل', validators=[Optional(), Length(max=200)])
    opposing_lawyer = StringField('محامي الطرف المقابل', validators=[Optional(), Length(max=100)])
    start_date = DateField('تاريخ بداية القضية', default=datetime.utcnow().date())
    end_date = DateField('تاريخ انتهاء القضية', validators=[Optional()])
    next_hearing_date = DateField('تاريخ الجلسة القادمة', validators=[Optional()])
    next_hearing_time = StringField('وقت الجلسة القادمة', validators=[Optional()], render_kw={'placeholder': 'مثال: 10:30'})
    submit = SubmitField('حفظ')
    
    def __init__(self, original_case_number=None, *args, **kwargs):
        super(CaseForm, self).__init__(*args, **kwargs)
        self.original_case_number = original_case_number
        
        # Populate client choices
        self.client_id.choices = [(0, 'اختر العميل')] + [
            (c.id, c.full_name) for c in Client.query.order_by(Client.first_name).all()
        ]
        
        # Populate lawyer choices
        self.lawyer_id.choices = [(0, 'اختر المحامي')] + [
            (u.id, u.full_name) for u in User.query.filter(
                User.role.in_(['lawyer', 'admin'])
            ).order_by(User.first_name).all()
        ]
    
    def validate_case_number(self, case_number):
        if case_number.data != self.original_case_number:
            case = Case.query.filter_by(case_number=case_number.data).first()
            if case is not None:
                raise ValidationError('رقم القضية مستخدم بالفعل.')
    
    def validate_client_id(self, client_id):
        if client_id.data == 0:
            raise ValidationError('يرجى اختيار العميل.')
    
    def validate_lawyer_id(self, lawyer_id):
        if lawyer_id.data == 0:
            raise ValidationError('يرجى اختيار المحامي المسؤول.')

class CaseSearchForm(FlaskForm):
    search = StringField('البحث', validators=[DataRequired()])
    case_type = SelectField('نوع القضية', choices=[
        ('', 'جميع الأنواع'),
        ('civil', 'مدنية'),
        ('criminal', 'جنائية'),
        ('commercial', 'تجارية'),
        ('administrative', 'إدارية'),
        ('labor', 'عمالية'),
        ('family', 'أحوال شخصية'),
        ('real_estate', 'عقارية'),
        ('other', 'أخرى')
    ])
    status = SelectField('الحالة', choices=[
        ('', 'جميع الحالات'),
        ('active', 'نشطة'),
        ('closed', 'مغلقة'),
        ('suspended', 'معلقة')
    ])
    submit = SubmitField('بحث')
