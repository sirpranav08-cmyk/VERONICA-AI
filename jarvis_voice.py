"""
VERONICA Voice Engine v2 — Natural neural TTS with emotion + message queue
Replaces agent/jarvis_voice.py  (same public API: speak, speak_async, detect_emotion, clean_text)

Upgrades:
  * Piper neural TTS (en_US-amy, a natural female voice, runs 100% offline on CPU)
    -> fallback: legacy PowerShell System.Speech (Zira) if Piper isn't set up yet
  * Message QUEUE instead of the `_speaking` lock — before, any message spoken while
    she was talking was silently DROPPED (lost reminders/notifications). Now they queue.
  * Emotion controls speed + volume + variation instead of only Zira's robotic Rate slider
  * Mutes the always-on mic while she speaks (kills the echo loop where she heard herself)
  * stop_speaking() to interrupt her instantly

SETUP (one time):
    pip install piper-tts soundfile
    python download_voice.py
"""
import os
import re
import sys
import queue
import shutil
import threading
import subprocess
import tempfile

VOICE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "data", "piper_voice")
MODEL_PATH = os.path.join(VOICE_DIR, "en_US-amy-medium.onnx")

EMOTION_RULES = [
    (["excellent", "amazing", "fantastic", "congratulations", "great job",
      "well done", "perfect", "awesome", "brilliant", "outstanding",
      "you did it", "success", "completed successfully"],
     {"rate": 3, "style": "excited"}),
    (["good morning", "good afternoon", "good evening", "hello pranav",
      "hi pranav", "welcome back", "good to see", "nice to meet",
      "how are you", "hope you"],
     {"rate": 2, "style": "cheerful"}),
    (["sorry", "unfortunately", "i apologize", "failed", "error occurred",
      "something went wrong", "couldn't", "unable to", "my apologies",
      "i understand", "that must be"],
     {"rate": 0, "style": "empathetic"}),
    (["reminder", "don't forget", "upcoming", "tomorrow", "exam",
      "contest", "deadline", "scheduled", "you have", "just a reminder"],
     {"rate": 1, "style": "hopeful"}),
    (["warning", "danger", "alert", "critical", "important", "attention",
      "be careful", "watch out", "security"],
     {"rate": -1, "style": "serious"}),
    (["did you know", "interesting", "fascinating", "actually", "fun fact",
      "surprisingly", "research shows", "studies"],
     {"rate": 1, "style": "curious"}),
    (["here are", "i found", "according to", "the result", "system info",
      "cpu", "ram", "memory", "you have", "emails", "reminders"],
     {"rate": 1, "style": "confident"}),
]
DEFAULT_EMOTION = {"rate": 1, "style": "friendly"}

# legacy rate (-1..3) -> (piper length_scale<1=faster, volume, noise/variation)
_PIPER_MAP = {
    3:  (0.82, 1.25, 0.80),   # excited: fast, loud, expressive
    2:  (0.90, 1.12, 0.70),   # cheerful
    1:  (1.00, 1.00, 0.55),   # neutral/friendly
    0:  (1.12, 0.92, 0.40),   # empathetic: slower, softer
    -1: (1.25, 0.88, 0.30),   # serious: slow, low
}


def detect_emotion(text: str) -> dict:
    lower = text.lower()
    for keywords, emotion in EMOTION_RULES:
        if any(w in lower for w in keywords):
            return emotion
    return DEFAULT_EMOTION


def clean_text(text: str) -> str:
    text = re.sub(r'http[s]?://\S+', '', text)
    text = re.sub(r'[A-Za-z]:\\[\w\\\.\-]+', '', text)
    text = re.sub(r'Executing \w+\.\.\.', '', text)
    text = re.sub(r'[⚙*#`•\-_>|]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:450]


# ── Piper backend ─────────────────────────────────────────────────
def _piper_available() -> bool:
    return os.path.exists(MODEL_PATH) and os.path.exists(MODEL_PATH + ".json")


def _piper_cmd():
    exe = shutil.which("piper")
    return [exe] if exe else [sys.executable, "-m", "piper"]


def _play_wav(path: str):
    try:
        import sounddevice as sd
        import soundfile as sf
        data, sr = sf.read(path)
        sd.play(data, sr)
        sd.wait()
        return
    except Exception:
        pass
    ps = f"(New-Object Media.SoundPlayer '{path}').PlaySync()"
    subprocess.run(["powershell", "-WindowStyle", "Hidden", "-Command", ps],
                   timeout=180)


def _speak_piper(text: str, emo: dict) -> bool:
    if not _piper_available():
        return False
    length, volume, noise = _PIPER_MAP.get(emo.get("rate", 1), _PIPER_MAP[1])
    out = os.path.join(tempfile.gettempdir(), "veronica_tts.wav")
    cmd = _piper_cmd() + [
        "--model", MODEL_PATH,
        "--output_file", out,
        "--length-scale", str(length),
        "--noise-scale", str(noise),
        "--volume", str(volume),
    ]
    print(f"[Voice] Piper ({emo['style']}): {text[:50]}...")
    p = subprocess.run(cmd, input=text.encode("utf-8"),
                       capture_output=True, timeout=60)
    if p.returncode != 0 or not os.path.exists(out):
        print(f"[Voice] Piper failed: {p.stderr.decode(errors='ignore')[:200]}")
        return False
    _play_wav(out)
    return True


# ── Legacy fallback (original Zira engine) ────────────────────────
def _speak_legacy(text: str, emo: dict):
    safe = text.replace("'", " ").replace('"', ' ').replace('\n', ' ')
    rate = emo.get("rate", 1)
    print(f"[Voice] Legacy Zira ({emo['style']}): {safe[:50]}...")
    script = f"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice('Microsoft Zira Desktop')
$s.Rate = {rate}
$s.Volume = 100
$s.Speak('{safe}')
$s.Dispose()
"""
    subprocess.run(["powershell", "-WindowStyle", "Hidden", "-Command", script],
                   timeout=60, capture_output=True)


# ── Mic mute while speaking (kills echo loop) ─────────────────────
def _set_mic_listening(listening: bool):
    try:
        import always_on_mic
        always_on_mic.set_speaking(not listening)
    except Exception:
        pass


# ── Queue: nothing gets dropped anymore ───────────────────────────
_q = queue.Queue()
_worker_on = False


def _worker():
    while True:
        text = _q.get()
        try:
            _speak_now(text)
        except Exception as e:
            print(f"[Voice] Error: {e}")
        finally:
            _q.task_done()


def _ensure_worker():
    global _worker_on
    if not _worker_on:
        _worker_on = True
        threading.Thread(target=_worker, daemon=True).start()


def _speak_now(text: str):
    clean = clean_text(text)
    if not clean or len(clean) < 3:
        return
    emo = detect_emotion(clean)
    _set_mic_listening(False)
    try:
        if not _speak_piper(clean, emo):
            _speak_legacy(clean, emo)
    finally:
        _set_mic_listening(True)


def speak(text: str, emotion: str = None):
    """Speak immediately (blocks until done)."""
    _speak_now(text)


def speak_async(text: str, emotion: str = None):
    """Queue a message — it WILL be spoken, in order, even mid-sentence."""
    _ensure_worker()
    _q.put(text)


def stop_speaking():
    """Interrupt current speech and clear pending queue."""
    while not _q.empty():
        try:
            _q.get_nowait()
            _q.task_done()
        except queue.Empty:
            break
    try:
        import sounddevice as sd
        sd.stop()
    except Exception:
        pass
    subprocess.run(["powershell", "-WindowStyle", "Hidden", "-Command",
                    "Get-Process piper -ErrorAction SilentlyContinue | Stop-Process -Force"],
                   capture_output=True)


# ── convenience wrappers (kept for compatibility) ─────────────────
def speak_excited(text): speak_async(text)
def speak_cheerful(text): speak_async(text)
def speak_sad(text): speak_async(text)
def speak_calm(text): speak_async(text)


if __name__ == "__main__":
    print("Testing VERONICA v2 voice...\n")
    for t in [
        "Good morning Sir! All systems are online and ready for today.",
        "Excellent! Your task was completed successfully!",
        "I'm sorry, something went wrong with that request.",
        "Just a reminder — your LeetCode contest is tomorrow at 7:30 AM!",
        "Warning! High CPU usage detected, Sir.",
    ]:
        speak(t)
        import time
        time.sleep(0.3)