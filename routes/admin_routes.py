from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps
from models import db
from models.user import User
from models.document import Document
from models.access_log import AccessLog
from datetime import datetime, timedelta
from sqlalchemy import func
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db
from models.user import User
from models.document import Document
from models.access_log import AccessLog
from routes import admin_bp  # Import from routes package
from functools import wraps
admin_bp = Blueprint('admin', __name__)
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Admin access required', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    # Stats
    total_users = User.query.count()
    total_docs = Document.query.count()
    total_views = AccessLog.query.count()
    
    # Recent activity
    recent_views = AccessLog.query.order_by(AccessLog.viewed_at.desc()).limit(10).all()
    
    # Active documents
    active_docs = Document.query.filter(
        Document.is_active == True,
        Document.expiry_time > datetime.utcnow()
    ).count()
    
    # Storage used
    total_size = db.session.query(func.sum(Document.file_size)).scalar() or 0
    total_size_mb = total_size / (1024 * 1024)
    
    # Chart data
    last_7_days = []
    for i in range(6, -1, -1):
        date = datetime.utcnow().date() - timedelta(days=i)
        count = AccessLog.query.filter(
            func.date(AccessLog.viewed_at) == date
        ).count()
        last_7_days.append({
            'date': date.strftime('%Y-%m-%d'),
            'views': count
        })
    
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         total_docs=total_docs,
                         total_views=total_views,
                         active_docs=active_docs,
                         total_size_mb=round(total_size_mb, 2),
                         recent_views=recent_views,
                         chart_data=last_7_days)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', users=users)

@admin_bp.route('/documents')
@login_required
@admin_required
def documents():
    documents = Document.query.order_by(Document.created_at.desc()).all()
    return render_template('admin_documents.html', documents=documents)

@admin_bp.route('/logs')
@login_required
@admin_required
def logs():
    page = request.args.get('page', 1, type=int)
    logs = AccessLog.query.order_by(AccessLog.viewed_at.desc()).paginate(page=page, per_page=50)
    return render_template('admin_logs.html', logs=logs)

@admin_bp.route('/user/<int:user_id>/toggle')
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Cannot deactivate yourself', 'danger')
    else:
        user.is_active = not user.is_active
        db.session.commit()
        flash(f'User {user.username} {"activated" if user.is_active else "deactivated"}', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/document/<int:doc_id>/delete')
@login_required
@admin_required
def delete_document(doc_id):
    document = Document.query.get_or_404(doc_id)
    
    # Delete file
    import os
    try:
        os.remove(document.file_path)
    except OSError:
        pass
    
    db.session.delete(document)
    db.session.commit()
    
    flash('Document deleted', 'success')
    return redirect(url_for('admin.documents'))

@admin_bp.route('/stats')
@login_required
@admin_required
def stats():
    # Daily active users
    dau = AccessLog.query.filter(
        AccessLog.viewed_at >= datetime.utcnow() - timedelta(days=1)
    ).distinct(AccessLog.user_id).count()
    
    # Weekly active users
    wau = AccessLog.query.filter(
        AccessLog.viewed_at >= datetime.utcnow() - timedelta(days=7)
    ).distinct(AccessLog.user_id).count()
    
    # Monthly active users
    mau = AccessLog.query.filter(
        AccessLog.viewed_at >= datetime.utcnow() - timedelta(days=30)
    ).distinct(AccessLog.user_id).count()
    
    # Top documents
    top_docs = db.session.query(
        Document.original_filename,
        func.count(AccessLog.id).label('view_count')
    ).join(AccessLog).group_by(Document.id).order_by(func.count(AccessLog.id).desc()).limit(5).all()
    
    return jsonify({
        'dau': dau,
        'wau': wau,
        'mau': mau,
        'top_documents': [{'name': d[0], 'views': d[1]} for d in top_docs]
    })
