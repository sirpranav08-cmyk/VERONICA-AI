"""
"""
Global wake word listener - runs in background
Listens for "Hey JARVIS" anywhere on Windows
Opens JARVIS desktop app when detected
"""
import sounddevice as sd
import numpy as np
import subprocess
import os
import sys
import time
from faster_whisper import WhisperModel

WAKE_WORDS = ["jarvis", "hey jarvis", "hi jarvis", "ok jarvis"]
SAMPLE_RATE = 16000
CHUNK_DURATION = 2  # Listen in 2 second chunks
THRESHOLD = 300     # Min volume to trigger transcription

model = None

def load_model():
    global model
    if model is None:
        print("[Wake] Loading Whisper tiny model...")
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        print("[Wake] Model ready - listening for 'Hey JARVIS'...")
    return model

def is_jarvis_open():
    """Check if JARVIS desktop app is already running."""
    result = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq electron.exe"],
        capture_output=True, text=True
    )
    return "electron.exe" in result.stdout

def open_jarvis():
    """Open JARVIS desktop app."""
    if not is_jarvis_open():
        print("[Wake] Opening JARVIS...")
        subprocess.Popen(
            [r"D:\jarvis-agent\desktop\node_modules\electron\dist\electron.exe", "."],
            cwd=r"D:\jarvis-agent\desktop",
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    else:
        print("[Wake] JARVIS already open - bringing to front")
        # Bring window to front using PowerShell
        subprocess.run([
            "powershell", "-Command",
            "(Get-Process electron).MainWindowHandle | ForEach-Object { [void][System.Runtime.InteropServices.Marshal]::GetFunctionPointerForDelegate((New-Object System.Windows.Forms.NativeWindow)) }"
        ], capture_output=True)

def listen_loop():
    load_model()
    print("[Wake] Global wake word listener started")
    print("[Wake] Say 'Hey JARVIS' to open the app")

    while True:
        try:
            # Record a short chunk
            audio = sd.rec(
                int(CHUNK_DURATION * SAMPLE_RATE),
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype='int16'
            )
            sd.wait()

            # Check volume - skip silent chunks
            volume = abs(audio).max()
            if volume < THRESHOLD:
                continue

            # Transcribe
            import scipy.io.wavfile as wav
            import tempfile
            tmp = os.path.join(tempfile.gettempdir(), "jarvis_wake.wav")
            wav.write(tmp, SAMPLE_RATE, audio)

            segments, _ = model.transcribe(tmp, language="en")
            text = " ".join(s.text for s in segments).strip().lower()

            if text:
                print(f"[Wake] Heard: {text}")

            # Check for wake word
            if any(w in text for w in WAKE_WORDS):
                print(f"[Wake] WAKE WORD DETECTED: {text}")
                open_jarvis()
                time.sleep(3)  # Cooldown

        except Exception as e:
            print(f"[Wake] Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    listen_loop()
