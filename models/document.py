from datetime import datetime
from . import db

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # in bytes
    file_type = db.Column(db.String(50))
    
    # Security
    token = db.Column(db.String(100), unique=True, nullable=False)
    view_limit = db.Column(db.Integer, default=10)
    view_count = db.Column(db.Integer, default=0)
    expiry_time = db.Column(db.DateTime)
    watermark_enabled = db.Column(db.Boolean, default=True)
    password_protected = db.Column(db.Boolean, default=False)
    document_password = db.Column(db.String(200), nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_accessed = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    access_logs = db.relationship('AccessLog', backref='document', lazy=True, cascade='all, delete-orphan')
    
    def is_expired(self):
        if self.expiry_time:
            return datetime.utcnow() > self.expiry_time
        return False
    
    def can_access(self):
        if not self.is_active:
            return False
        if self.is_expired():
            return False
        if self.view_limit and self.view_count >= self.view_limit:
            return False
        return True
    
    def increment_view(self):
        self.view_count += 1
        self.last_accessed = datetime.utcnow()
    
    def __repr__(self):
        return f'<Document {self.filename}>'
