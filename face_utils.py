import face_recognition
import numpy as np
import cv2
import base64
import os
from PIL import Image
import io


def encode_face_from_image_path(image_path):
    """Load image from path and return face encoding."""
    try:
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)
        if encodings:
            return encodings[0]
        return None
    except Exception as e:
        print(f"Error encoding face: {e}")
        return None


def encode_face_from_base64(base64_string):
    """Decode base64 image and return face encoding."""
    try:
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        image_data = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_data)).convert('RGB')
        image_np = np.array(image)
        
        encodings = face_recognition.face_encodings(image_np)
        if encodings:
            return encodings[0]
        return None
    except Exception as e:
        print(f"Error encoding face from base64: {e}")
        return None


def save_face_image(base64_string, save_dir, filename):
    """Save base64 image to disk and return path."""
    try:
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]

        image_data = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_data)).convert('RGB')
        
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, filename)
        image.save(filepath, 'JPEG', quality=90)
        return filepath
    except Exception as e:
        print(f"Error saving face image: {e}")
        return None


def recognize_face(base64_string, known_students, tolerance=0.5):
    """
    Compare captured face against all known student encodings.
    Returns (student, confidence) or (None, None).
    """
    try:
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]

        image_data = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_data)).convert('RGB')
        image_np = np.array(image)

        # Detect faces in the captured image
        face_locations = face_recognition.face_locations(image_np)
        if not face_locations:
            return None, None, "no_face"

        unknown_encodings = face_recognition.face_encodings(image_np, face_locations)
        if not unknown_encodings:
            return None, None, "no_encoding"

        unknown_encoding = unknown_encodings[0]

        best_match = None
        best_distance = 1.0

        for student in known_students:
            encoding = student.get_face_encoding()
            if encoding is None:
                continue

            distance = face_recognition.face_distance([encoding], unknown_encoding)[0]
            if distance < best_distance:
                best_distance = distance
                best_match = student

        if best_match and best_distance <= tolerance:
            confidence = round((1 - best_distance) * 100, 1)
            return best_match, confidence, "match"
        
        return None, None, "no_match"

    except Exception as e:
        print(f"Error recognizing face: {e}")
        return None, None, "error"


def detect_face_in_frame(base64_string):
    """Check if a face is present in the frame (for live detection feedback)."""
    try:
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]

        image_data = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_data)).convert('RGB')
        image_np = np.array(image)

        face_locations = face_recognition.face_locations(image_np)
        return len(face_locations) > 0, face_locations
    except Exception:
        return False, []
