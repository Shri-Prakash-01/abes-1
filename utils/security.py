import re
import secrets
import hashlib
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """
    Password requirements:
    - At least 8 characters
    - At least one uppercase
    - At least one lowercase
    - At least one number
    """
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    return True

def generate_token(length=32):
    """Generate secure random token"""
    return secrets.token_urlsafe(length)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'docx', 'xlsx', 'txt'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_client_ip():
    """Get real client IP behind proxy"""
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0]
    return request.remote_addr

def hash_file(file_path):
    """Generate SHA-256 hash of file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def parse_user_agent(user_agent_string):
    """Parse user agent string"""
    ua = user_agent_string.lower()
    
    # Browser detection
    browsers = {
        'chrome': 'chrome' in ua and 'edg' not in ua,
        'firefox': 'firefox' in ua,
        'safari': 'safari' in ua and 'chrome' not in ua and 'android' not in ua,
        'edge': 'edg' in ua,
        'opera': 'opr' in ua or 'opera' in ua,
        'ie': 'msie' in ua or 'trident' in ua
    }
    browser = next((b for b, v in browsers.items() if v), 'unknown')
    
    # OS detection
    os_list = {
        'windows': 'windows' in ua,
        'mac': 'mac' in ua and 'ios' not in ua,
        'linux': 'linux' in ua,
        'android': 'android' in ua,
        'ios': 'iphone' in ua or 'ipad' in ua or 'ipod' in ua
    }
    os_name = next((os for os, v in os_list.items() if v), 'unknown')
    
    # Device detection
    if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
        device = 'mobile'
    elif 'tablet' in ua or 'ipad' in ua:
        device = 'tablet'
    else:
        device = 'desktop'
    
    return {
        'browser': browser.capitalize(),
        'os': os_name.capitalize(),
        'device': device
    }

def sanitize_filename(filename):
    """Remove dangerous characters from filename"""
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    return filename

def check_rate_limit(ip_address, endpoint, limit=100, period=3600):
    """Basic rate limiting check"""
    # Implementation would use Redis or database
    # Placeholder for now
    return True

def generate_csrf_token():
    """Generate CSRF token"""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(16)
    return session['_csrf_token']
