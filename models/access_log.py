from datetime import datetime
from . import db

class AccessLog(db.Model):
    __tablename__ = 'access_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Access details
    viewer_ip = db.Column(db.String(50))
    viewer_email = db.Column(db.String(120))
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Security events
    screenshot_detected = db.Column(db.Boolean, default=False)
    devtools_opened = db.Column(db.Boolean, default=False)
    right_click_attempt = db.Column(db.Boolean, default=False)
    
    # Device info
    user_agent = db.Column(db.String(500))
    browser = db.Column(db.String(100))
    os = db.Column(db.String(100))
    device_type = db.Column(db.String(50))
    
    def __repr__(self):
        return f'<AccessLog Doc:{self.document_id} IP:{self.viewer_ip}>'
