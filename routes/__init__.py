from flask import Blueprint

auth_bp = Blueprint('auth', __name__)
doc_bp = Blueprint('doc', __name__)
admin_bp = Blueprint('admin', __name__)

from . import auth_routes, document_routes, admin_routes
