from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateTimeField, SubmitField
from wtforms.validators import DataRequired, Optional, Length
from app.models import Case, Client, User
from datetime import datetime

class AppointmentForm(FlaskForm):
    title = StringField('عنوان الموعد', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('الوصف', validators=[Optional()])
    appointment_type = SelectField('نوع الموعد', choices=[
        ('hearing', 'جلسة محكمة'),
        ('meeting', 'اجتماع'),
        ('consultation', 'استشارة'),
        ('other', 'أخرى')
    ], validators=[DataRequired()])
    start_time = DateTimeField('وقت البداية', validators=[DataRequired()], 
                              format='%Y-%m-%dT%H:%M')
    end_time = DateTimeField('وقت النهاية', validators=[DataRequired()], 
                            format='%Y-%m-%dT%H:%M')
    location = StringField('المكان', validators=[Optional(), Length(max=200)])
    status = SelectField('الحالة', choices=[
        ('scheduled', 'مجدول'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي')
    ], default='scheduled')
    case_id = SelectField('القضية', coerce=int, validators=[Optional()])
    client_id = SelectField('العميل', coerce=int, validators=[Optional()])
    notes = TextAreaField('ملاحظات', validators=[Optional()])
    submit = SubmitField('حفظ')
    
    def __init__(self, *args, **kwargs):
        super(AppointmentForm, self).__init__(*args, **kwargs)
        
        # Populate case choices
        self.case_id.choices = [(0, 'اختر القضية (اختياري)')] + [
            (c.id, f"{c.case_number} - {c.title}") 
            for c in Case.query.filter_by(status='active').order_by(Case.case_number).all()
        ]
        
        # Populate client choices
        self.client_id.choices = [(0, 'اختر العميل (اختياري)')] + [
            (c.id, c.full_name) for c in Client.query.order_by(Client.first_name).all()
        ]
    
    def validate_end_time(self, end_time):
        if end_time.data <= self.start_time.data:
            raise ValidationError('وقت النهاية يجب أن يكون بعد وقت البداية.')

class AppointmentSearchForm(FlaskForm):
    search = StringField('البحث')
    appointment_type = SelectField('نوع الموعد', choices=[
        ('', 'جميع الأنواع'),
        ('hearing', 'جلسة محكمة'),
        ('meeting', 'اجتماع'),
        ('consultation', 'استشارة'),
        ('other', 'أخرى')
    ])
    status = SelectField('الحالة', choices=[
        ('', 'جميع الحالات'),
        ('scheduled', 'مجدول'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي')
    ])
    submit = SubmitField('بحث')
