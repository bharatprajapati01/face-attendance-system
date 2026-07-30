from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import pickle

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # 'admin' or 'student'
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    student = db.relationship('Student', backref='user', foreign_keys=[student_id])

    def __init__(self, username=None, password_hash=None, role='student', student_id=None, **kwargs):
        if username is not None: self.username = username
        if password_hash is not None: self.password_hash = password_hash
        if role is not None: self.role = role
        if student_id is not None: self.student_id = student_id
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return f'<User {self.username}>'


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    roll_number = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    photo_path = db.Column(db.String(256), nullable=True)
    face_encoding = db.Column(db.LargeBinary, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    attendance_records = db.relationship('Attendance', backref='student', lazy=True,
                                         cascade='all, delete-orphan')

    def set_face_encoding(self, encoding):
        self.face_encoding = pickle.dumps(encoding)

    def get_face_encoding(self):
        if self.face_encoding:
            return pickle.loads(self.face_encoding)
        return None

    def get_attendance_percentage(self):
        total = len(self.attendance_records)
        if total == 0:
            return 0
        present = sum(1 for a in self.attendance_records if a.status == 'present')
        return round((present / total) * 100, 1)

    def __init__(self, name=None, roll_number=None, email=None, class_name=None, phone=None, photo_path=None, face_encoding=None, **kwargs):
        if name is not None: self.name = name
        if roll_number is not None: self.roll_number = roll_number
        if email is not None: self.email = email
        if class_name is not None: self.class_name = class_name
        if phone is not None: self.phone = phone
        if photo_path is not None: self.photo_path = photo_path
        if face_encoding is not None: self.face_encoding = face_encoding
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return f'<Student {self.name}>'


class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    entry_time = db.Column(db.DateTime, nullable=True)
    exit_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='present')
    marked_by = db.Column(db.String(50), default='face_recognition')

    def duration_minutes(self):
        if self.entry_time and self.exit_time:
            delta = self.exit_time - self.entry_time
            return round(delta.total_seconds() / 60, 1)
        return None

    def __init__(self, student_id=None, date=None, entry_time=None, exit_time=None, status='present', marked_by='face_recognition', **kwargs):
        if student_id is not None: self.student_id = student_id
        if date is not None: self.date = date
        if entry_time is not None: self.entry_time = entry_time
        if exit_time is not None: self.exit_time = exit_time
        if status is not None: self.status = status
        if marked_by is not None: self.marked_by = marked_by
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return f'<Attendance student={self.student_id} date={self.date}>'
