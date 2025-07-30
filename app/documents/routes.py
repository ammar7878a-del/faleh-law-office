import os
import uuid
from flask import render_template, redirect, url_for, flash, request, current_app, send_file, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.documents import bp
from app.documents.forms import DocumentForm, DocumentEditForm, DocumentSearchForm
from app.models import Document, Case, Client
from datetime import datetime

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif'}

@bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    document_type = request.args.get('document_type', '', type=str)
    case_id = request.args.get('case_id', 0, type=int)
    client_id = request.args.get('client_id', 0, type=int)
    is_confidential = request.args.get('is_confidential', '', type=str)
    
    query = Document.query
    
    # Apply filters
    if search:
        query = query.filter(
            db.or_(
                Document.original_filename.contains(search),
                Document.description.contains(search),
                Document.tags.contains(search)
            )
        )
    
    if document_type:
        query = query.filter(Document.document_type == document_type)
    
    if case_id:
        query = query.filter(Document.case_id == case_id)
    
    if client_id:
        query = query.filter(Document.client_id == client_id)
    
    if is_confidential:
        query = query.filter(Document.is_confidential == (is_confidential == '1'))
    
    documents = query.order_by(Document.created_at.desc()).paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    
    next_url = url_for('documents.index', page=documents.next_num, search=search,
                      document_type=document_type, case_id=case_id, client_id=client_id,
                      is_confidential=is_confidential) if documents.has_next else None
    prev_url = url_for('documents.index', page=documents.prev_num, search=search,
                      document_type=document_type, case_id=case_id, client_id=client_id,
                      is_confidential=is_confidential) if documents.has_prev else None
    
    return render_template('documents/index.html', title='المستندات',
                         documents=documents.items, next_url=next_url, prev_url=prev_url,
                         search=search, document_type=document_type, case_id=case_id,
                         client_id=client_id, is_confidential=is_confidential)

@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = DocumentForm()
    if form.validate_on_submit():
        file = form.file.data
        if file and allowed_file(file.filename):
            # Generate unique filename
            filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
            
            # Create upload directory if it doesn't exist
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            # Save file
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Create document record
            document = Document(
                filename=filename,
                original_filename=secure_filename(file.filename),
                file_path=file_path,
                file_size=file_size,
                file_type=file.filename.rsplit('.', 1)[1].lower(),
                document_type=form.document_type.data,
                description=form.description.data,
                tags=form.tags.data,
                is_confidential=form.is_confidential.data,
                case_id=form.case_id.data if form.case_id.data != 0 else None,
                client_id=form.client_id.data if form.client_id.data != 0 else None,
                uploaded_by=current_user.id
            )
            
            db.session.add(document)
            db.session.commit()
            
            flash(f'تم رفع المستند "{document.original_filename}" بنجاح', 'success')
            return redirect(url_for('documents.view', id=document.id))
        else:
            flash('نوع الملف غير مدعوم', 'danger')
    
    return render_template('documents/upload.html', title='رفع مستند جديد', form=form)

@bp.route('/<int:id>')
@login_required
def view(id):
    document = Document.query.get_or_404(id)
    
    # Check if user can view confidential documents
    if document.is_confidential and current_user.role not in ['admin', 'lawyer']:
        flash('ليس لديك صلاحية لعرض هذا المستند السري', 'danger')
        return redirect(url_for('documents.index'))
    
    return render_template('documents/view.html', 
                         title=f'المستند: {document.original_filename}',
                         document=document)

@bp.route('/<int:id>/download')
@login_required
def download(id):
    document = Document.query.get_or_404(id)
    
    # Check if user can download confidential documents
    if document.is_confidential and current_user.role not in ['admin', 'lawyer']:
        flash('ليس لديك صلاحية لتحميل هذا المستند السري', 'danger')
        return redirect(url_for('documents.index'))
    
    if not os.path.exists(document.file_path):
        flash('الملف غير موجود', 'danger')
        return redirect(url_for('documents.view', id=id))
    
    if request.args.get('preview') == 'true':
        # For preview, redirect to the uploads URL
        return redirect(url_for('uploaded_file', filename=os.path.basename(document.file_path)))
    else:
        # For download, send as attachment
        response = send_file(document.file_path, as_attachment=True,
                          download_name=document.original_filename)
        response.headers['Content-Type'] = 'application/octet-stream'
        response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{document.original_filename}'
        return response

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    document = Document.query.get_or_404(id)
    
    # Check permissions
    if current_user.role not in ['admin', 'lawyer'] and document.uploaded_by != current_user.id:
        flash('ليس لديك صلاحية لتعديل هذا المستند', 'danger')
        return redirect(url_for('documents.view', id=id))
    
    form = DocumentEditForm()
    
    if form.validate_on_submit():
        document.document_type = form.document_type.data
        document.description = form.description.data
        document.tags = form.tags.data
        document.is_confidential = form.is_confidential.data
        document.case_id = form.case_id.data if form.case_id.data != 0 else None
        document.client_id = form.client_id.data if form.client_id.data != 0 else None
        
        db.session.commit()
        flash(f'تم تحديث المستند "{document.original_filename}" بنجاح', 'success')
        return redirect(url_for('documents.view', id=document.id))
    
    elif request.method == 'GET':
        form.document_type.data = document.document_type
        form.description.data = document.description
        form.tags.data = document.tags
        form.is_confidential.data = document.is_confidential
        form.case_id.data = document.case_id or 0
        form.client_id.data = document.client_id or 0
    
    return render_template('documents/edit.html', 
                         title=f'تعديل المستند: {document.original_filename}',
                         form=form, document=document)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    document = Document.query.get_or_404(id)
    
    # Check permissions
    if current_user.role not in ['admin'] and document.uploaded_by != current_user.id:
        flash('ليس لديك صلاحية لحذف هذا المستند', 'danger')
        return redirect(url_for('documents.view', id=id))
    
    # Delete file from filesystem
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    document_name = document.original_filename
    db.session.delete(document)
    db.session.commit()
    
    flash(f'تم حذف المستند "{document_name}" بنجاح', 'success')
    return redirect(url_for('documents.index'))
