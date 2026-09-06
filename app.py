from flask import Flask
from flask_login import LoginManager
from config import Config
from models import db, User, Student
from werkzeug.security import generate_password_hash
import os

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure dirs exist
    os.makedirs(os.path.join(app.root_path, 'database'), exist_ok=True)
    os.makedirs(app.config['KNOWN_FACES_DIR'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from auth import auth_bp
    from admin import admin_bp
    from student import student_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(student_bp)

    # Create tables and seed admin
    with app.app_context():
        db.create_all()
        _seed_admin()

    return app


def _seed_admin():
    """Create default admin if none exists."""
    if not User.query.filter_by(role='admin').first():
        
        admin_password = os.environ.get("ADMIN_PASSWORD")

        if not admin_password:
            raise RuntimeError("ADMIN_PASSWORD environment variable is required")

        admin = User(
        username='admin',
        password_hash=generate_password_hash(admin_password),
        role='admin'
        )
        db.session.add(admin)
        db.session.commit()

        print("Default admin created: username=admin")


if __name__ == '__main__':
    app = create_app()
    print("Face Attendance System running at http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
