from flask import Flask, render_template
from flask_login import LoginManager
from flask_mail import Mail
from config import Config
from models import db
from datetime import datetime
from models.user import User
import os

# Initialize extensions
login_manager = LoginManager()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # Login manager setup
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.document_routes import doc_bp
    from routes.admin_routes import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(doc_bp, url_prefix='/doc')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Root route
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/loading')
    def loading():
        return render_template('loading.html')
    
    # Create tables
    with app.app_context():
        db.create_all()
        # Create admin if not exists
        from models.user import User
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@securevault.com',
                role='admin'
            )
            admin.set_password('Admin123!')
            db.session.add(admin)
            db.session.commit()
        # Add context processor for templates
    @app.context_processor
    def utility_processor():
        return {'now': datetime.utcnow}
    return app

# This is the important part for Render
app = create_app()

if __name__ == '__main__':
    # For local development
    app.run(debug=True, host='0.0.0.0', port=5000)
else:
    # For production (Render) - get port from environment variable
    import os
    port = int(os.environ.get('PORT', 10000))
    # Note: In production, you don't call app.run() here
    # Gunicorn will run the 'app' object directly
