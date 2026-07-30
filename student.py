from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Student, Attendance
from face_utils import recognize_face
from datetime import datetime, date, timedelta
from sqlalchemy import func
from functools import wraps

student_bp = Blueprint('student', __name__, url_prefix='/student')


def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('Student access required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    student = current_user.student
    if not student:
        flash('Student profile not found.', 'error')
        return redirect(url_for('auth.logout'))

    today = date.today()
    
    # Today's attendance
    today_record = Attendance.query.filter_by(
        student_id=student.id, date=today
    ).first()

    # Last 30 days stats
    start_date = today - timedelta(days=29)
    records_30 = Attendance.query.filter(
        Attendance.student_id == student.id,
        Attendance.date >= start_date
    ).all()

    present_30 = sum(1 for r in records_30 if r.status == 'present')
    attendance_pct = round((present_30 / 30) * 100, 1) if records_30 else 0

    # Streak
    streak = 0
    check_date = today
    while True:
        rec = Attendance.query.filter_by(student_id=student.id, date=check_date).first()
        if rec and rec.status == 'present':
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    # Last 7 days data for mini chart
    weekly_labels = []
    weekly_data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        rec = Attendance.query.filter_by(student_id=student.id, date=day).first()
        weekly_labels.append(day.strftime('%a'))
        weekly_data.append(1 if rec and rec.status == 'present' else 0)

    # Recent records
    recent = Attendance.query.filter_by(student_id=student.id).order_by(
        Attendance.date.desc()
    ).limit(5).all()

    # Monthly calendar data for heatmap
    month_start = today.replace(day=1)
    month_records = Attendance.query.filter(
        Attendance.student_id == student.id,
        Attendance.date >= month_start
    ).all()
    present_dates = [r.date.day for r in month_records if r.status == 'present']

    return render_template('student/dashboard.html',
                           student=student,
                           today_record=today_record,
                           attendance_pct=attendance_pct,
                           present_30=present_30,
                           streak=streak,
                           weekly_labels=weekly_labels,
                           weekly_data=weekly_data,
                           recent=recent,
                           present_dates=present_dates,
                           today=today)


@student_bp.route('/mark-attendance')
@login_required
@student_required
def mark_attendance():
    student = current_user.student
    today = date.today()
    today_record = Attendance.query.filter_by(student_id=student.id, date=today).first()
    return render_template('student/mark_attendance.html',
                           student=student,
                           today_record=today_record,
                           today=today)


@student_bp.route('/api/recognize', methods=['POST'])
@login_required
@student_required
def api_recognize():
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({'success': False, 'message': 'No image data provided'})

    image_data = data['image']
    student = current_user.student

    # Get all known students for recognition
    all_students = Student.query.filter(Student.face_encoding != None).all()

    matched_student, confidence, status = recognize_face(image_data, all_students)

    if status == 'no_face':
        return jsonify({'success': False, 'message': 'No face detected. Please look at the camera.', 'status': 'no_face'})
    
    if status == 'no_match':
        return jsonify({'success': False, 'message': 'Face not recognized. Please try again.', 'status': 'no_match'})
    
    if status in ('no_encoding', 'error'):
        return jsonify({'success': False, 'message': 'Recognition error. Please try again.', 'status': status})

    if matched_student.id != student.id:
        return jsonify({'success': False, 'message': 'Face does not match your registered photo.', 'status': 'mismatch'})

    # Log attendance
    today = date.today()
    now = datetime.utcnow()

    existing = Attendance.query.filter_by(student_id=student.id, date=today).first()

    if not existing:
        # First scan → Entry
        record = Attendance(
            student_id=student.id,
            date=today,
            entry_time=now,
            status='present'
        )
        db.session.add(record)
        db.session.commit()
        return jsonify({
            'success': True,
            'action': 'entry',
            'message': f'Entry recorded at {now.strftime("%I:%M %p")}',
            'student_name': student.name,
            'confidence': confidence,
            'time': now.strftime('%I:%M:%S %p')
        })
    elif not existing.exit_time:
        # Second scan → Exit
        existing.exit_time = now
        db.session.commit()
        duration = existing.duration_minutes()
        return jsonify({
            'success': True,
            'action': 'exit',
            'message': f'Exit recorded at {now.strftime("%I:%M %p")}',
            'student_name': student.name,
            'confidence': confidence,
            'time': now.strftime('%I:%M:%S %p'),
            'duration': duration
        })
    else:
        return jsonify({
            'success': True,
            'action': 'already_done',
            'message': 'Attendance already fully recorded for today.',
            'student_name': student.name,
            'confidence': confidence
        })


@student_bp.route('/history')
@login_required
@student_required
def history():
    student = current_user.student
    page = request.args.get('page', 1, type=int)
    month_filter = request.args.get('month', '')

    query = Attendance.query.filter_by(student_id=student.id)
    if month_filter:
        from datetime import datetime
        try:
            m = datetime.strptime(month_filter, '%Y-%m')
            query = query.filter(
                func.strftime('%Y-%m', Attendance.date) == month_filter
            )
        except ValueError:
            pass

    records = query.order_by(Attendance.date.desc()).paginate(page=page, per_page=15)
    
    total = query.count()
    present = query.filter(Attendance.status == 'present').count()
    
    return render_template('student/history.html',
                           student=student,
                           records=records,
                           total=total,
                           present=present,
                           month_filter=month_filter)
