from flask import render_template, redirect, url_for, flash, request, send_file, jsonify
from flask_login import login_required, current_user
from models import db
from models.document import Document
from models.access_log import AccessLog
from routes import doc_bp
from utils.link_generator import generate_token, generate_secure_link
from utils.watermark import add_watermark, add_watermark_to_pdf, add_watermark_to_image
import os
from datetime import datetime, timedelta
from config import Config
import secrets
from werkzeug.utils import secure_filename

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'docx', 'xlsx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@doc_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        # Check if file was uploaded
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # Secure filename and generate unique name
            original_filename = secure_filename(file.filename)
            file_ext = original_filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{secrets.token_hex(16)}.{file_ext}"
            
            # Ensure upload folder exists
            upload_folder = os.path.join(Config.UPLOAD_FOLDER)
            os.makedirs(upload_folder, exist_ok=True)
            
            # Save file
            file_path = os.path.join(upload_folder, unique_filename)
            file.save(file_path)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Determine file type properly
            if file.content_type:
                file_type = file.content_type
            else:
                # Guess based on extension
                mime_types = {
                    'pdf': 'application/pdf',
                    'png': 'image/png',
                    'jpg': 'image/jpeg',
                    'jpeg': 'image/jpeg',
                    'gif': 'image/gif',
                    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'txt': 'text/plain'
                }
                file_type = mime_types.get(file_ext, f'application/{file_ext}')
            
            # Get form data
            view_limit = request.form.get('view_limit', type=int)
            expiry_days = request.form.get('expiry_days', type=int, default=7)
            watermark_enabled = request.form.get('watermark_enabled') == 'on'
            
            # Calculate expiry date
            expiry_time = datetime.utcnow() + timedelta(days=expiry_days) if expiry_days else None
            
            # Generate unique token
            token = generate_token()
            
            # Create document record
            document = Document(
                owner_id=current_user.id,
                filename=unique_filename,
                original_filename=original_filename,
                file_path=file_path,
                file_size=file_size,
                file_type=file_type,
                token=token,
                view_limit=view_limit,
                view_count=0,
                expiry_time=expiry_time,
                watermark_enabled=watermark_enabled,
                created_at=datetime.utcnow()
            )
            
            db.session.add(document)
            db.session.commit()
            
            flash('Document uploaded successfully!', 'success')
            return render_template('upload_success.html', document=document)
        else:
            flash('File type not allowed. Please upload PDF, images, or documents.', 'error')
            return redirect(request.url)
    
    return render_template('upload.html')

@doc_bp.route('/view/<token>')
def view(token):
    """View a document with watermarking"""
    document = Document.query.filter_by(token=token).first()
    
    # Check if document exists
    if not document:
        flash('Invalid or expired link.', 'error')
        return redirect(url_for('index'))
    
    # Check expiry
    if document.expiry_time and document.expiry_time < datetime.utcnow():
        flash('This link has expired.', 'error')
        return redirect(url_for('index'))
    
    # Check view limit
    if document.view_limit and document.view_count >= document.view_limit:
        flash('View limit exceeded.', 'error')
        return redirect(url_for('index'))
    
    # Log access
    log = AccessLog(
        document_id=document.id,
        viewer_ip=request.remote_addr,
        viewer_email=current_user.email if current_user.is_authenticated else 'Guest',
        viewed_at=datetime.utcnow()
    )
    db.session.add(log)
    document.view_count += 1
    db.session.commit()
    
    # For watermarked viewing, we might need to serve a watermarked version
    if document.watermark_enabled:
        watermark_text = f"{current_user.email if current_user.is_authenticated else 'Guest'} - {request.remote_addr} - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
        watermarked_path = add_watermark(document.file_path, watermark_text)
        # Use the watermarked path if needed
    
    # Use unified template for both images and PDFs
    return render_template('view_document.html', document=document)

@doc_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard showing their documents"""
    documents = Document.query.filter_by(owner_id=current_user.id).order_by(Document.created_at.desc()).all()
    
    # Get statistics
    total_documents = len(documents)
    total_views = sum(doc.view_count for doc in documents)
    active_links = sum(1 for doc in documents if not doc.expiry_time or doc.expiry_time > datetime.utcnow())
    expired_links = sum(1 for doc in documents if doc.expiry_time and doc.expiry_time <= datetime.utcnow())
    
    # Create stats object for template
    stats = {
        'total': total_documents,
        'views': total_views,
        'active': active_links,
        'expired': expired_links
    }
    
    return render_template('dashboard.html', 
                         documents=documents,
                         stats=stats,
                         now=datetime.utcnow)

@doc_bp.route('/delete/<int:doc_id>')
@login_required
def delete(doc_id):
    """Delete a document"""
    document = Document.query.get_or_404(doc_id)
    
    # Check if user owns the document
    if document.owner_id != current_user.id and not current_user.is_admin():
        flash('You do not have permission to delete this document.', 'error')
        return redirect(url_for('doc.dashboard'))
    
    # Delete file from filesystem
    try:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
    except Exception as e:
        flash(f'Error deleting file: {str(e)}', 'error')
    
    # Delete from database
    db.session.delete(document)
    db.session.commit()
    
    flash('Document deleted successfully.', 'success')
    return redirect(url_for('doc.dashboard'))

@doc_bp.route('/revoke/<int:doc_id>')
@login_required
def revoke(doc_id):
    """Revoke access by setting expiry to now"""
    document = Document.query.get_or_404(doc_id)
    
    # Check if user owns the document
    if document.owner_id != current_user.id and not current_user.is_admin():
        flash('You do not have permission to revoke this document.', 'error')
        return redirect(url_for('doc.dashboard'))
    
    # Set expiry to now
    document.expiry_time = datetime.utcnow()
    db.session.commit()
    
    flash('Document access revoked successfully.', 'success')
    return redirect(url_for('doc.dashboard'))

@doc_bp.route('/regenerate/<int:doc_id>')
@login_required
def regenerate(doc_id):
    """Generate a new token for the document"""
    document = Document.query.get_or_404(doc_id)
    
    # Check if user owns the document
    if document.owner_id != current_user.id and not current_user.is_admin():
        flash('You do not have permission to regenerate this link.', 'error')
        return redirect(url_for('doc.dashboard'))
    
    # Generate new token
    document.token = generate_token()
    # Reset view count if needed
    document.view_count = 0
    # Extend expiry if needed
    if document.expiry_time and document.expiry_time < datetime.utcnow():
        document.expiry_time = datetime.utcnow() + timedelta(days=7)
    
    db.session.commit()
    
    flash('New secure link generated successfully.', 'success')
    return redirect(url_for('doc.dashboard'))

@doc_bp.route('/screenshot-detected', methods=['POST'])
def screenshot_detected():
    """Log screenshot attempts"""
    data = request.get_json()
    document_id = data.get('document_id')
    
    if document_id:
        # Find the most recent access log for this document
        log = AccessLog.query.filter_by(document_id=document_id).order_by(AccessLog.viewed_at.desc()).first()
        if log:
            log.screenshot_detected = True
            db.session.commit()
            
            # You could also send an email alert to the owner here
            
            return jsonify({'status': 'logged'}), 200
    
    return jsonify({'status': 'error'}), 400

@doc_bp.route('/download/<int:doc_id>')
@login_required
def download(doc_id):
    """Download the original document"""
    document = Document.query.get_or_404(doc_id)
    
    # Check if user owns the document
    if document.owner_id != current_user.id and not current_user.is_admin():
        flash('You do not have permission to download this document.', 'error')
        return redirect(url_for('doc.dashboard'))
    
    return send_file(document.file_path, 
                    as_attachment=True, 
                    download_name=document.original_filename)

@doc_bp.route('/share/<int:doc_id>')
@login_required
def share(doc_id):
    """Generate sharing link"""
    document = Document.query.get_or_404(doc_id)
    
    # Check if user owns the document
    if document.owner_id != current_user.id and not current_user.is_admin():
        flash('You do not have permission to share this document.', 'error')
        return redirect(url_for('doc.dashboard'))
    
    share_link = url_for('doc.view', token=document.token, _external=True)
    
    return jsonify({
        'share_link': share_link,
        'token': document.token,
        'expiry': document.expiry_time.isoformat() if document.expiry_time else None
    })

@doc_bp.route('/preview/<int:doc_id>')
@login_required
def preview(doc_id):
    """Preview document without counting view"""
    document = Document.query.get_or_404(doc_id)
    
    # Check if user owns the document
    if document.owner_id != current_user.id and not current_user.is_admin():
        flash('You do not have permission to preview this document.', 'error')
        return redirect(url_for('doc.dashboard'))
    
    return render_template('view_document.html', document=document, preview_mode=True)
