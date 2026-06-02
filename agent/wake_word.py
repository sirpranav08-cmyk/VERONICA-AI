"""
Global wake word listener - runs in background
Listens for "Hey JARVIS" anywhere on Windows
Opens JARVIS desktop app when detected
"""
import sounddevice as sd
import numpy as np
import subprocess
import os
import time
import tempfile
import scipy.io.wavfile as wav
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
CHUNK_DURATION = 2
THRESHOLD = 200

JARVIS_VARIANTS = [
    "jarvis", "hey jarvis", "hi jarvis", "ok jarvis",
    "javi", "harvey", "harris", "paris", "horace",
    "boris", "davis", "service", "h-o-r-s", "george",
    "jorge", "hey service", "hey harris", "hey harvey"
]

model = None

def load_model():
    global model
    if model is None:
        print("[Wake] Loading Whisper tiny model...")
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        print("[Wake] Model ready — listening for 'Hey JARVIS'...")
    return model

def is_jarvis_open():
    result = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq electron.exe"],
        capture_output=True, text=True
    )
    return "electron.exe" in result.stdout

def open_jarvis():
    if not is_jarvis_open():
        print("[Wake] Opening JARVIS...")
        subprocess.Popen(
            [r"D:\jarvis-agent\desktop\node_modules\electron\dist\electron.exe", "."],
            cwd=r"D:\jarvis-agent\desktop",
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    else:
        print("[Wake] JARVIS already open")

def listen_loop():
    load_model()
    print("[Wake] Global wake word listener started")
    print("[Wake] Say 'Hey JARVIS' to open the app")

    while True:
        try:
            # Record chunk
            audio = sd.rec(
                int(CHUNK_DURATION * SAMPLE_RATE),
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype='int16'
            )
            sd.wait()

            # Skip silent chunks
            volume = abs(audio).max()
            if volume < THRESHOLD:
                continue

            # Transcribe
            tmp = os.path.join(tempfile.gettempdir(), "jarvis_wake.wav")
            wav.write(tmp, SAMPLE_RATE, audio)
            segments, _ = model.transcribe(tmp, language="en")
            text = " ".join(s.text for s in segments).strip().lower()

            if text:
                print(f"[Wake] Heard: {text}")

            # Check for wake word
            if any(w in text for w in JARVIS_VARIANTS):
                print(f"[Wake] WAKE WORD DETECTED!")
                open_jarvis()
                time.sleep(3)  # Cooldown

        except Exception as e:
            print(f"[Wake] Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    listen_loop()