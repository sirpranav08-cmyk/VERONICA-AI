"""
VERONICA Always-On Face Watch
Continuously monitors camera and recognizes faces
"""
import cv2
import numpy as np
import threading
import time
import subprocess
from pathlib import Path

CASCADE_PATH = "D:/jarvis-agent/agent/data/haarcascade.xml"
TRAINED_MODEL = Path("D:/jarvis-agent/agent/data/face_model.yml")
LABELS_FILE = Path("D:/jarvis-agent/agent/data/face_labels.txt")

detector = cv2.CascadeClassifier(CASCADE_PATH)
recognizer = cv2.face.LBPHFaceRecognizer_create()
labels = {}

# State
last_seen = None
last_seen_time = 0
away_notified = False
welcome_notified = False
AWAY_TIMEOUT = 30  # seconds before "user left" alert
CHECK_INTERVAL = 0.5  # seconds between checks

def load_model():
    global labels
    if TRAINED_MODEL.exists():
        recognizer.read(str(TRAINED_MODEL))
    if LABELS_FILE.exists():
        for line in LABELS_FILE.read_text().splitlines():
            if ':' in line:
                lid, name = line.split(':', 1)
                labels[int(lid)] = name
    print(f"[FaceWatch] Loaded {len(labels)} face(s)")

def notify(title: str, msg: str):
    script = f'''
Add-Type -AssemblyName System.Windows.Forms
$n = New-Object System.Windows.Forms.NotifyIcon
$n.Icon = [System.Drawing.SystemIcons]::Information
$n.Visible = $true
$n.BalloonTipTitle = "{title}"
$n.BalloonTipText = "{msg}"
$n.ShowBalloonTip(4000)
'''
    subprocess.Popen(
        ["powershell", "-WindowStyle", "Hidden", "-Command", script],
        creationflags=subprocess.CREATE_NO_WINDOW
    )

def auto_lock():
    """Lock PC when user leaves."""
    subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])

def watch_forever(show_window: bool = False):
    global last_seen, last_seen_time, away_notified, welcome_notified

    load_model()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[FaceWatch] Camera not found!")
        return

    print("[FaceWatch] Always-on face watch started...")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    cap.set(cv2.CAP_PROP_FPS, 15)

    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(1)
            continue

        frame_count += 1
        # Only process every 5th frame for speed
        if frame_count % 5 != 0:
            if show_window:
                cv2.imshow("VERONICA — Face Watch", frame)
                cv2.waitKey(1)
            time.sleep(0.05)
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(
            gray, scaleFactor=1.2, minNeighbors=5,
            minSize=(60, 60)
        )

        detected_name = None

        for (x, y, w, h) in faces:
            face_img = cv2.resize(gray[y:y+h, x:x+w], (100, 100))
            try:
                if labels:
                    label_id, confidence = recognizer.predict(face_img)
                    if confidence < 75:
                        detected_name = labels.get(label_id, "Unknown")
                    else:
                        detected_name = "Unknown"
                else:
                    detected_name = "Someone"
            except:
                detected_name = "Someone"

            if show_window:
                color = (0, 245, 100) if detected_name not in ["Unknown","Someone"] else (0, 0, 255)
                cv2.rectangle(frame, (x,y), (x+w,y+h), color, 2)
                cv2.putText(frame, detected_name or "?",
                           (x, y-8), cv2.FONT_HERSHEY_SIMPLEX,
                           0.6, color, 2)

        now = time.time()

        # ── Someone recognized ────────────────────────────────────
        if detected_name and detected_name not in ["Unknown", "Someone"]:
            if last_seen != detected_name:
                # New person detected
                print(f"[FaceWatch] Recognized: {detected_name}")
                notify("VERONICA", f"Welcome back, {detected_name}!")
                welcome_notified = True
                away_notified = False
            last_seen = detected_name
            last_seen_time = now

        elif detected_name == "Unknown":
            if last_seen and last_seen not in ["Unknown", "Someone"]:
                print(f"[FaceWatch] Unknown person detected!")
                notify("VERONICA ⚠", "Unknown person detected at your PC!")

        # ── User left detection ───────────────────────────────────
        if last_seen and (now - last_seen_time) > AWAY_TIMEOUT:
            if not away_notified:
                print(f"[FaceWatch] {last_seen} left — auto locking...")
                notify("VERONICA", f"{last_seen} left — locking screen.")
                auto_lock()
                away_notified = True
                welcome_notified = False
                last_seen = None

        if show_window:
            # HUD overlay
            cv2.putText(frame, "VERONICA FACE WATCH",
                       (5, 15), cv2.FONT_HERSHEY_SIMPLEX,
                       0.45, (0, 245, 255), 1)
            status = f"Watching: {last_seen or 'No one'}"
            cv2.putText(frame, status,
                       (5, 230), cv2.FONT_HERSHEY_SIMPLEX,
                       0.4, (0, 200, 200), 1)
            cv2.imshow("VERONICA — Face Watch", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        time.sleep(CHECK_INTERVAL)

    cap.release()
    if show_window:
        cv2.destroyAllWindows()

def start(show_window: bool = False):
    """Start face watch in background thread."""
    t = threading.Thread(
        target=watch_forever,
        args=(show_window,),
        daemon=True
    )
    t.start()
    print("[FaceWatch] Background face watch started")
    return t

if __name__ == "__main__":
    # Run with visible window for testing
    watch_forever(show_window=True)