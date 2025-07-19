from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, DecimalField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange, ValidationError
from app.models import Invoice, Client, Case
from datetime import datetime, timedelta
from decimal import Decimal

class InvoiceForm(FlaskForm):
    invoice_number = StringField('رقم الفاتورة', validators=[DataRequired(), Length(max=50)])
    description = TextAreaField('الوصف', validators=[Optional()])
    amount = DecimalField('المبلغ', validators=[DataRequired(), NumberRange(min=0)], places=2)
    tax_amount = DecimalField('مبلغ الضريبة', validators=[Optional(), NumberRange(min=0)], 
                             places=2, default=Decimal('0.00'))
    status = SelectField('الحالة', choices=[
        ('pending', 'معلقة'),
        ('paid', 'مدفوعة'),
        ('overdue', 'متأخرة'),
        ('cancelled', 'ملغية')
    ], default='pending')
    client_id = SelectField('العميل', coerce=int, validators=[DataRequired()])
    case_id = SelectField('القضية', coerce=int, validators=[Optional()])
    issue_date = DateField('تاريخ الإصدار', default=datetime.utcnow().date())
    due_date = DateField('تاريخ الاستحقاق', 
                        default=(datetime.utcnow() + timedelta(days=30)).date())
    paid_date = DateField('تاريخ الدفع', validators=[Optional()])
    payment_method = SelectField('طريقة الدفع', choices=[
        ('', 'لم يتم الدفع'),
        ('cash', 'نقداً'),
        ('bank_transfer', 'تحويل بنكي'),
        ('check', 'شيك'),
        ('credit_card', 'بطاقة ائتمان')
    ])
    notes = TextAreaField('ملاحظات', validators=[Optional()])
    submit = SubmitField('حفظ')
    
    def __init__(self, original_invoice_number=None, *args, **kwargs):
        super(InvoiceForm, self).__init__(*args, **kwargs)
        self.original_invoice_number = original_invoice_number
        
        # Populate client choices
        self.client_id.choices = [(0, 'اختر العميل')] + [
            (c.id, c.full_name) for c in Client.query.order_by(Client.first_name).all()
        ]
        
        # Populate case choices
        self.case_id.choices = [(0, 'اختر القضية (اختياري)')] + [
            (c.id, f"{c.case_number} - {c.title}") 
            for c in Case.query.filter_by(status='active').order_by(Case.case_number).all()
        ]
    
    def validate_invoice_number(self, invoice_number):
        if invoice_number.data != self.original_invoice_number:
            invoice = Invoice.query.filter_by(invoice_number=invoice_number.data).first()
            if invoice is not None:
                raise ValidationError('رقم الفاتورة مستخدم بالفعل.')
    
    def validate_client_id(self, client_id):
        if client_id.data == 0:
            raise ValidationError('يرجى اختيار العميل.')
    
    def validate_due_date(self, due_date):
        if due_date.data < self.issue_date.data:
            raise ValidationError('تاريخ الاستحقاق يجب أن يكون بعد تاريخ الإصدار.')
    
    def validate_paid_date(self, paid_date):
        if paid_date.data and paid_date.data < self.issue_date.data:
            raise ValidationError('تاريخ الدفع يجب أن يكون بعد تاريخ الإصدار.')

class InvoiceSearchForm(FlaskForm):
    search = StringField('البحث')
    status = SelectField('الحالة', choices=[
        ('', 'جميع الحالات'),
        ('pending', 'معلقة'),
        ('paid', 'مدفوعة'),
        ('overdue', 'متأخرة'),
        ('cancelled', 'ملغية')
    ])
    client_id = SelectField('العميل', coerce=int)
    submit = SubmitField('بحث')
    
    def __init__(self, *args, **kwargs):
        super(InvoiceSearchForm, self).__init__(*args, **kwargs)
        
        # Populate client choices
        self.client_id.choices = [(0, 'جميع العملاء')] + [
            (c.id, c.full_name) for c in Client.query.order_by(Client.first_name).all()
        ]
