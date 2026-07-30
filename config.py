import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'face-attendance-super-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'database', 'attendance.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    KNOWN_FACES_DIR = os.path.join(BASE_DIR, 'known_faces')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    FACE_RECOGNITION_TOLERANCE = 0.5
