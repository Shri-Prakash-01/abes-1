import secrets
import string
import random
from datetime import datetime, timedelta

def generate_token(length=32):
    """Generate a secure random token"""
    return secrets.token_urlsafe(length)

def generate_secure_link(length=32):
    """Generate a secure link token"""
    return secrets.token_urlsafe(length)  # Same as generate_token

def generate_short_token(length=8):
    """Generate a shorter token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(random.choice(alphabet) for _ in range(length))

def generate_expiry_date(days=7):
    """Generate expiry date"""
    return datetime.utcnow() + timedelta(days=days)

def validate_token(token):
    """Validate token"""
    if not token or len(token) < 8:
        return False
    return True
