"""
VERONICA Fast Face Auth using OpenCV
Lightweight and instant
"""
import cv2
import numpy as np
import os
import time
import urllib.request
from pathlib import Path

FACES_DIR = Path("D:/jarvis-agent/agent/data/faces")
FACES_DIR.mkdir(parents=True, exist_ok=True)

# OpenCV face detector - built in, no downloads needed
CASCADE_PATH = None
for path in [
    r"C:\Users\Admin\AppData\Local\Programs\Python\Python314\Lib\site-packages\cv2\data\haarcascade_frontalface_default.xml",
    r"D:\jarvis-agent\agent\.venv\Lib\site-packages\cv2\data\haarcascade_frontalface_default.xml",
]:
    if os.path.exists(path):
        CASCADE_PATH = path
        break

if not CASCADE_PATH:
    # Download it
    CASCADE_PATH = "D:/jarvis-agent/agent/data/haarcascade.xml"
    try:
        urllib.request.urlretrieve(
            "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml",
            CASCADE_PATH
        )
        print(f"[Face] Downloaded cascade to {CASCADE_PATH}")
    except Exception as e:
        print(f"[Face] Could not download cascade - face auth disabled ({e})")

detector = cv2.CascadeClassifier(CASCADE_PATH) if CASCADE_PATH else None
recognizer = cv2.face.LBPHFaceRecognizer_create()

TRAINED_MODEL = Path("D:/jarvis-agent/agent/data/face_model.yml")
LABELS_FILE = Path("D:/jarvis-agent/agent/data/face_labels.txt")

labels = {}  # id -> name

def load_model():
    global labels
    if TRAINED_MODEL.exists():
        recognizer.read(str(TRAINED_MODEL))
    if LABELS_FILE.exists():
        for line in LABELS_FILE.read_text().splitlines():
            if ':' in line:
                lid, name = line.split(':', 1)
                labels[int(lid)] = name

def save_model():
    recognizer.write(str(TRAINED_MODEL))
    LABELS_FILE.write_text(
        '\n'.join(f"{k}:{v}" for k, v in labels.items())
    )

def register_face(name: str = "Pranav") -> str:
    if detector is None:
        return "Face detector unavailable, Sir."

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return "Camera not found, Sir."

    person_dir = FACES_DIR / name
    person_dir.mkdir(exist_ok=True)

    count = 0
    needed = 100
    print(f"[Face] Capturing {needed} frames for {name}...")

    while count < needed:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            face_img = gray[y:y+h, x:x+w]
            face_img = cv2.resize(face_img, (100, 100))
            path = person_dir / f"{count}.jpg"
            cv2.imwrite(str(path), face_img)
            count += 1
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, f"Capturing: {count}/{needed}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 245, 100), 2)
        cv2.imshow("VERONICA — Register", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    if count < 5:
        return "No face detected, Sir. Try again in better lighting."

    # Assign a fresh label id (never reuse an existing one)
    label_id = max(labels.keys()) + 1 if labels else 0
    labels[label_id] = name

    # CRITICAL FIX: retrain on ALL saved faces, not just the new person,
    # because recognizer.train() replaces the previous training entirely.
    faces_data, ids = [], []
    for lid, person in labels.items():
        for img_path in (FACES_DIR / person).glob("*.jpg"):
            img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
            if img is not None:
                faces_data.append(img)
                ids.append(lid)

    recognizer.train(faces_data, np.array(ids))
    save_model()
    return f"Face registered for {name}, Sir! {count} samples captured."

def authenticate_face(timeout: int = 8) -> tuple:
    load_model()
    if detector is None or not labels:
        return False, "No faces registered or detector unavailable"

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return False, "No camera"

    start = time.time()
    result = (False, "Unknown")

    while time.time() - start < timeout:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            face_img = cv2.resize(gray[y:y+h, x:x+w], (100, 100))
            try:
                label_id, confidence = recognizer.predict(face_img)
                # Lower confidence = better match
                if confidence < 70:
                    name = labels.get(label_id, "Unknown")
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 245, 100), 2)
                    cv2.putText(frame, f"{name} {100-confidence:.0f}%",
                                (x, y-10), cv2.FONT_HERSHEY_SIMPLEX,
                                0.7, (0, 245, 100), 2)
                    cv2.imshow("VERONICA Auth", frame)
                    cv2.waitKey(300)
                    result = (True, name)
                    break
                else:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                    cv2.putText(frame, "Unknown",
                                (x, y-10), cv2.FONT_HERSHEY_SIMPLEX,
                                0.7, (0, 0, 255), 2)
            except cv2.error:
                pass

        t_left = int(timeout - (time.time() - start))
        cv2.putText(frame, f"VERONICA Auth — {t_left}s",
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 245, 255), 2)
        cv2.imshow("VERONICA Auth", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        if result[0]:
            break

    cap.release()
    cv2.destroyAllWindows()
    return result

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "register":
        name = sys.argv[2] if len(sys.argv) > 2 else "Pranav"
        print(register_face(name))
    else:
        load_model()
        print(authenticate_face())