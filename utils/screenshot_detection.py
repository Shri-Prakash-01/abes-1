from datetime import datetime
from models import db
from models.access_log import AccessLog

def log_screenshot_attempt(document_id, ip_address, method='unknown', user_id=None):
    """
    Log screenshot detection attempt
    """
    try:
        # Find the most recent access log for this document and IP
        access_log = AccessLog.query.filter_by(
            document_id=document_id,
            viewer_ip=ip_address
        ).order_by(AccessLog.viewed_at.desc()).first()
        
        if access_log:
            access_log.screenshot_detected = True
            db.session.commit()
            return True
    except Exception as e:
        print(f"Error logging screenshot: {e}")
    
    return False

def get_screenshot_stats(document_id):
    """
    Get screenshot attempt statistics for a document
    """
    try:
        total_attempts = AccessLog.query.filter_by(
            document_id=document_id,
            screenshot_detected=True
        ).count()
        
        unique_ips = db.session.query(AccessLog.viewer_ip).filter_by(
            document_id=document_id,
            screenshot_detected=True
        ).distinct().count()
        
        return {
            'total_attempts': total_attempts,
            'unique_ips': unique_ips
        }
    except Exception as e:
        print(f"Error getting stats: {e}")
        return {'total_attempts': 0, 'unique_ips': 0}

def check_screenshot_risk(document_id, threshold=3):
    """
    Check if document has high screenshot risk
    """
    stats = get_screenshot_stats(document_id)
    return stats['total_attempts'] >= threshold
