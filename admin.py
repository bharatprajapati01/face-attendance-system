from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from functools import wraps
from models import db, User, Student, Attendance
from face_utils import encode_face_from_base64, save_face_image
from datetime import datetime, date, timedelta
from sqlalchemy import func
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    today = date.today()
    total_students = Student.query.count()
    
    # Today's attendance
    today_present = db.session.query(func.count(Attendance.id)).filter(
        Attendance.date == today,
        Attendance.status == 'present'
    ).scalar() or 0
    
    today_percentage = round((today_present / total_students * 100), 1) if total_students > 0 else 0
    
    # Weekly attendance data (last 7 days)
    weekly_data = []
    weekly_labels = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = db.session.query(func.count(Attendance.id)).filter(
            Attendance.date == day,
            Attendance.status == 'present'
        ).scalar() or 0
        weekly_data.append(count)
        weekly_labels.append(day.strftime('%a'))
    
    # Monthly trend (last 30 days)
    monthly_data = []
    monthly_labels = []
    for i in range(29, -1, -1):
        day = today - timedelta(days=i)
        count = db.session.query(func.count(Attendance.id)).filter(
            Attendance.date == day,
            Attendance.status == 'present'
        ).scalar() or 0
        monthly_data.append(count)
        monthly_labels.append(day.strftime('%d %b'))
    
    # Recent attendance records
    recent_records = db.session.query(Attendance, Student).join(Student).order_by(
        Attendance.entry_time.desc()
    ).limit(10).all()
    
    # Students with no face encoding
    no_face_count = Student.query.filter(Student.face_encoding == None).count()
    
    return render_template('admin/dashboard.html',
                           total_students=total_students,
                           today_present=today_present,
                           today_percentage=today_percentage,
                           weekly_data=weekly_data,
                           weekly_labels=weekly_labels,
                           monthly_data=monthly_data,
                           monthly_labels=monthly_labels,
                           recent_records=recent_records,
                           no_face_count=no_face_count,
                           today=today)


@admin_bp.route('/students')
@login_required
@admin_required
def students():
    search = request.args.get('search', '')
    class_filter = request.args.get('class', '')
    
    query = Student.query
    if search:
        query = query.filter(
            (Student.name.ilike(f'%{search}%')) |
            (Student.roll_number.ilike(f'%{search}%')) |
            (Student.email.ilike(f'%{search}%'))
        )
    if class_filter:
        query = query.filter(Student.class_name == class_filter)
    
    students_list = query.order_by(Student.created_at.desc()).all()
    classes = db.session.query(Student.class_name).distinct().all()
    classes = [c[0] for c in classes]
    
    return render_template('admin/students.html',
                           students=students_list,
                           classes=classes,
                           search=search,
                           class_filter=class_filter)


@admin_bp.route('/students/add', methods=['POST'])
@login_required
@admin_required
def add_student():
    name = request.form.get('name', '').strip()
    roll_number = request.form.get('roll_number', '').strip()
    email = request.form.get('email', '').strip()
    class_name = request.form.get('class_name', '').strip()
    phone = request.form.get('phone', '').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    face_image = request.form.get('face_image', '')

    # Validate
    if not all([name, roll_number, email, class_name, username, password]):
        flash('All required fields must be filled.', 'error')
        return redirect(url_for('admin.students'))

    if Student.query.filter_by(roll_number=roll_number).first():
        flash(f'Roll number {roll_number} already exists.', 'error')
        return redirect(url_for('admin.students'))

    if User.query.filter_by(username=username).first():
        flash(f'Username {username} already taken.', 'error')
        return redirect(url_for('admin.students'))

    # Create student
    student = Student(
        name=name,
        roll_number=roll_number,
        email=email,
        class_name=class_name,
        phone=phone
    )

    # Handle face image
    if face_image:
        from config import Config
        photo_path = save_face_image(face_image, Config.KNOWN_FACES_DIR, f"{roll_number}.jpg")
        if photo_path:
            student.photo_path = photo_path
            encoding = encode_face_from_base64(face_image)
            if encoding is not None:
                student.set_face_encoding(encoding)

    db.session.add(student)
    db.session.flush()  # Get student ID

    # Create user account
    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        role='student',
        student_id=student.id
    )
    db.session.add(user)
    db.session.commit()

    flash(f'Student {name} added successfully!', 'success')
    return redirect(url_for('admin.students'))


@admin_bp.route('/students/<int:student_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    user = User.query.filter_by(student_id=student_id).first()
    
    if user:
        db.session.delete(user)
    
    # Remove photo
    if student.photo_path and os.path.exists(student.photo_path):
        os.remove(student.photo_path)
    
    db.session.delete(student)
    db.session.commit()
    flash(f'Student {student.name} deleted.', 'info')
    return redirect(url_for('admin.students'))


@admin_bp.route('/attendance')
@login_required
@admin_required
def attendance():
    date_filter = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    class_filter = request.args.get('class', '')
    
    try:
        filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
    except ValueError:
        filter_date = date.today()
    
    query = db.session.query(Attendance, Student).join(Student).filter(
        Attendance.date == filter_date
    )
    
    if class_filter:
        query = query.filter(Student.class_name == class_filter)
    
    records = query.order_by(Student.name).all()
    
    # Students without attendance today
    present_ids = [r[1].id for r in records]
    all_students = Student.query.all()
    absent_students = [s for s in all_students if s.id not in present_ids]
    
    classes = db.session.query(Student.class_name).distinct().all()
    classes = [c[0] for c in classes]
    
    return render_template('admin/attendance.html',
                           records=records,
                           absent_students=absent_students,
                           filter_date=filter_date,
                           date_filter=date_filter,
                           class_filter=class_filter,
                           classes=classes)


@admin_bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    today = date.today()
    total_students = Student.query.count()
    today_present = db.session.query(func.count(Attendance.id)).filter(
        Attendance.date == today,
        Attendance.status == 'present'
    ).scalar() or 0
    
    return jsonify({
        'total_students': total_students,
        'today_present': today_present,
        'today_absent': total_students - today_present,
        'today_percentage': round((today_present / total_students * 100), 1) if total_students > 0 else 0
    })
