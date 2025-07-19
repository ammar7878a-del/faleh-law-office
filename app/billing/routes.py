from flask import render_template, redirect, url_for, flash, request, current_app, make_response
from flask_login import login_required, current_user
from app import db
from app.billing import bp
from app.billing.forms import InvoiceForm, InvoiceSearchForm
from app.models import Invoice, Client, Case
from datetime import datetime
from decimal import Decimal
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfutils
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

@bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    status = request.args.get('status', '', type=str)
    client_id = request.args.get('client_id', 0, type=int)
    
    query = Invoice.query
    
    # Apply filters
    if search:
        query = query.filter(
            db.or_(
                Invoice.invoice_number.contains(search),
                Invoice.description.contains(search)
            )
        )
    
    if status:
        query = query.filter(Invoice.status == status)
    
    if client_id:
        query = query.filter(Invoice.client_id == client_id)
    
    invoices = query.order_by(Invoice.created_at.desc()).paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    
    next_url = url_for('billing.index', page=invoices.next_num, search=search,
                      status=status, client_id=client_id) if invoices.has_next else None
    prev_url = url_for('billing.index', page=invoices.prev_num, search=search,
                      status=status, client_id=client_id) if invoices.has_prev else None
    
    # Calculate totals
    total_pending = db.session.query(db.func.sum(Invoice.total_amount)).filter(
        Invoice.status == 'pending').scalar() or Decimal('0.00')
    total_paid = db.session.query(db.func.sum(Invoice.total_amount)).filter(
        Invoice.status == 'paid').scalar() or Decimal('0.00')
    total_overdue = db.session.query(db.func.sum(Invoice.total_amount)).filter(
        Invoice.status == 'overdue').scalar() or Decimal('0.00')
    
    return render_template('billing/index.html', title='الفوترة',
                         invoices=invoices.items, next_url=next_url, prev_url=prev_url,
                         search=search, status=status, client_id=client_id,
                         total_pending=total_pending, total_paid=total_paid,
                         total_overdue=total_overdue)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = InvoiceForm()
    if form.validate_on_submit():
        # Calculate total amount
        total_amount = form.amount.data + (form.tax_amount.data or Decimal('0.00'))
        
        invoice = Invoice(
            invoice_number=form.invoice_number.data,
            description=form.description.data,
            amount=form.amount.data,
            tax_amount=form.tax_amount.data or Decimal('0.00'),
            total_amount=total_amount,
            status=form.status.data,
            client_id=form.client_id.data,
            case_id=form.case_id.data if form.case_id.data != 0 else None,
            issue_date=form.issue_date.data,
            due_date=form.due_date.data,
            paid_date=form.paid_date.data,
            payment_method=form.payment_method.data,
            notes=form.notes.data
        )
        db.session.add(invoice)
        db.session.commit()
        flash(f'تم إضافة الفاتورة {invoice.invoice_number} بنجاح', 'success')
        return redirect(url_for('billing.view', id=invoice.id))
    
    return render_template('billing/form.html', title='إضافة فاتورة جديدة', form=form)

@bp.route('/<int:id>')
@login_required
def view(id):
    invoice = Invoice.query.get_or_404(id)
    return render_template('billing/view.html', title=f'الفاتورة: {invoice.invoice_number}',
                         invoice=invoice)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    invoice = Invoice.query.get_or_404(id)
    form = InvoiceForm(original_invoice_number=invoice.invoice_number)
    
    if form.validate_on_submit():
        # Calculate total amount
        total_amount = form.amount.data + (form.tax_amount.data or Decimal('0.00'))
        
        invoice.invoice_number = form.invoice_number.data
        invoice.description = form.description.data
        invoice.amount = form.amount.data
        invoice.tax_amount = form.tax_amount.data or Decimal('0.00')
        invoice.total_amount = total_amount
        invoice.status = form.status.data
        invoice.client_id = form.client_id.data
        invoice.case_id = form.case_id.data if form.case_id.data != 0 else None
        invoice.issue_date = form.issue_date.data
        invoice.due_date = form.due_date.data
        invoice.paid_date = form.paid_date.data
        invoice.payment_method = form.payment_method.data
        invoice.notes = form.notes.data
        
        db.session.commit()
        flash(f'تم تحديث الفاتورة {invoice.invoice_number} بنجاح', 'success')
        return redirect(url_for('billing.view', id=invoice.id))
    
    elif request.method == 'GET':
        form.invoice_number.data = invoice.invoice_number
        form.description.data = invoice.description
        form.amount.data = invoice.amount
        form.tax_amount.data = invoice.tax_amount
        form.status.data = invoice.status
        form.client_id.data = invoice.client_id
        form.case_id.data = invoice.case_id or 0
        form.issue_date.data = invoice.issue_date
        form.due_date.data = invoice.due_date
        form.paid_date.data = invoice.paid_date
        form.payment_method.data = invoice.payment_method
        form.notes.data = invoice.notes
    
    return render_template('billing/form.html', title=f'تعديل الفاتورة: {invoice.invoice_number}',
                         form=form, invoice=invoice)

@bp.route('/<int:id>/pdf')
@login_required
def generate_pdf(id):
    invoice = Invoice.query.get_or_404(id)
    
    # Create PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Add content to PDF
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 100, f"Invoice #{invoice.invoice_number}")
    
    p.setFont("Helvetica", 12)
    y = height - 150
    p.drawString(100, y, f"Client: {invoice.client.full_name}")
    y -= 20
    p.drawString(100, y, f"Issue Date: {invoice.issue_date}")
    y -= 20
    p.drawString(100, y, f"Due Date: {invoice.due_date}")
    y -= 40
    
    if invoice.description:
        p.drawString(100, y, f"Description: {invoice.description}")
        y -= 40
    
    p.drawString(100, y, f"Amount: {invoice.amount} SAR")
    y -= 20
    p.drawString(100, y, f"Tax: {invoice.tax_amount} SAR")
    y -= 20
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, y, f"Total: {invoice.total_amount} SAR")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=invoice_{invoice.invoice_number}.pdf'
    
    return response
