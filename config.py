import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or "sqlite:///" + os.path.join(BASE_DIR, "database", "attendance.db")
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    KNOWN_FACES_DIR = os.path.join(BASE_DIR, "known_faces")

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    FACE_RECOGNITION_TOLERANCE = float(
        os.environ.get("FACE_RECOGNITION_TOLERANCE", "0.5")
    )
