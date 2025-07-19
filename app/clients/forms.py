from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, Length, ValidationError
from app.models import Client

class ClientForm(FlaskForm):
    first_name = StringField('الاسم الأول', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('الاسم الأخير', validators=[DataRequired(), Length(max=64)])
    email = StringField('البريد الإلكتروني', validators=[Optional(), Email()])
    phone = StringField('رقم الهاتف', validators=[Optional(), Length(max=20)])
    mobile = StringField('رقم الجوال', validators=[Optional(), Length(max=20)])
    address = TextAreaField('العنوان', validators=[Optional()])
    national_id = StringField('رقم الهوية', validators=[Optional(), Length(max=20)])
    company = StringField('الشركة', validators=[Optional(), Length(max=100)])
    notes = TextAreaField('ملاحظات', validators=[Optional()])
    submit = SubmitField('حفظ')
    
    def __init__(self, original_national_id=None, *args, **kwargs):
        super(ClientForm, self).__init__(*args, **kwargs)
        self.original_national_id = original_national_id
    
    def validate_national_id(self, national_id):
        if national_id.data and national_id.data != self.original_national_id:
            client = Client.query.filter_by(national_id=national_id.data).first()
            if client is not None:
                raise ValidationError('رقم الهوية مستخدم بالفعل لعميل آخر.')

class ClientSearchForm(FlaskForm):
    search = StringField('البحث', validators=[DataRequired()])
    submit = SubmitField('بحث')
