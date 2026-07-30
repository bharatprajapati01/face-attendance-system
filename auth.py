from flask import Blueprint, render_template, request, redirect, url_for, flash, session
# pyrefly: ignore [missing-import]
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Student

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'student')

        user = User.query.filter_by(username=username, role=role).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            flash(f'Welcome back, {username}!', 'success')
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('student.dashboard'))
        else:
            flash('Invalid username, password, or role. Please try again.', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
