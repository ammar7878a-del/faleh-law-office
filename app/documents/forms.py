from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional, Length
from app.models import Case, Client

class DocumentForm(FlaskForm):
    file = FileField('الملف', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif'], 
                   'الملفات المسموحة: PDF, DOC, DOCX, TXT, JPG, PNG, GIF')
    ])
    document_type = SelectField('نوع المستند', choices=[
        ('contract', 'عقد'),
        ('evidence', 'دليل'),
        ('correspondence', 'مراسلات'),
        ('court_document', 'مستند محكمة'),
        ('identification', 'هوية'),
        ('financial', 'مالي'),
        ('legal_memo', 'مذكرة قانونية'),
        ('other', 'أخرى')
    ], validators=[DataRequired()])
    description = TextAreaField('الوصف', validators=[Optional()])
    tags = StringField('العلامات', validators=[Optional(), Length(max=500)],
                      description='افصل العلامات بفواصل')
    is_confidential = BooleanField('مستند سري')
    case_id = SelectField('القضية', coerce=int, validators=[Optional()])
    client_id = SelectField('العميل', coerce=int, validators=[Optional()])
    submit = SubmitField('رفع الملف')
    
    def __init__(self, *args, **kwargs):
        super(DocumentForm, self).__init__(*args, **kwargs)
        
        # Populate case choices
        self.case_id.choices = [(0, 'اختر القضية (اختياري)')] + [
            (c.id, f"{c.case_number} - {c.title}") 
            for c in Case.query.filter_by(status='active').order_by(Case.case_number).all()
        ]
        
        # Populate client choices
        self.client_id.choices = [(0, 'اختر العميل (اختياري)')] + [
            (c.id, c.full_name) for c in Client.query.order_by(Client.first_name).all()
        ]

class DocumentEditForm(FlaskForm):
    document_type = SelectField('نوع المستند', choices=[
        ('contract', 'عقد'),
        ('evidence', 'دليل'),
        ('correspondence', 'مراسلات'),
        ('court_document', 'مستند محكمة'),
        ('identification', 'هوية'),
        ('financial', 'مالي'),
        ('legal_memo', 'مذكرة قانونية'),
        ('other', 'أخرى')
    ], validators=[DataRequired()])
    description = TextAreaField('الوصف', validators=[Optional()])
    tags = StringField('العلامات', validators=[Optional(), Length(max=500)],
                      description='افصل العلامات بفواصل')
    is_confidential = BooleanField('مستند سري')
    case_id = SelectField('القضية', coerce=int, validators=[Optional()])
    client_id = SelectField('العميل', coerce=int, validators=[Optional()])
    submit = SubmitField('حفظ التغييرات')
    
    def __init__(self, *args, **kwargs):
        super(DocumentEditForm, self).__init__(*args, **kwargs)
        
        # Populate case choices
        self.case_id.choices = [(0, 'اختر القضية (اختياري)')] + [
            (c.id, f"{c.case_number} - {c.title}") 
            for c in Case.query.filter_by(status='active').order_by(Case.case_number).all()
        ]
        
        # Populate client choices
        self.client_id.choices = [(0, 'اختر العميل (اختياري)')] + [
            (c.id, c.full_name) for c in Client.query.order_by(Client.first_name).all()
        ]

class DocumentSearchForm(FlaskForm):
    search = StringField('البحث')
    document_type = SelectField('نوع المستند', choices=[
        ('', 'جميع الأنواع'),
        ('contract', 'عقد'),
        ('evidence', 'دليل'),
        ('correspondence', 'مراسلات'),
        ('court_document', 'مستند محكمة'),
        ('identification', 'هوية'),
        ('financial', 'مالي'),
        ('legal_memo', 'مذكرة قانونية'),
        ('other', 'أخرى')
    ])
    case_id = SelectField('القضية', coerce=int)
    client_id = SelectField('العميل', coerce=int)
    is_confidential = SelectField('السرية', choices=[
        ('', 'جميع المستندات'),
        ('1', 'سرية فقط'),
        ('0', 'غير سرية فقط')
    ])
    submit = SubmitField('بحث')
    
    def __init__(self, *args, **kwargs):
        super(DocumentSearchForm, self).__init__(*args, **kwargs)
        
        # Populate case choices
        self.case_id.choices = [(0, 'جميع القضايا')] + [
            (c.id, f"{c.case_number} - {c.title}") 
            for c in Case.query.order_by(Case.case_number).all()
        ]
        
        # Populate client choices
        self.client_id.choices = [(0, 'جميع العملاء')] + [
            (c.id, c.full_name) for c in Client.query.order_by(Client.first_name).all()
        ]
