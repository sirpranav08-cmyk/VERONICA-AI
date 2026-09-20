"""
VERONICA Voice Engine — Emotional Speech System
Auto-detects emotion from text and speaks with matching tone
"""
import subprocess
import re
import threading

_speaking = False
_lock = threading.Lock()

EMOTION_RULES = [
    # Excited / Happy
    (["excellent", "amazing", "fantastic", "congratulations", "great job",
      "well done", "perfect", "awesome", "brilliant", "outstanding",
      "you did it", "success", "completed successfully"],
     {"rate": 3, "pitch": "+10Hz", "style": "excited"}),

    # Cheerful / Greeting
    (["good morning", "good afternoon", "good evening", "hello pranav",
      "hi pranav", "welcome back", "good to see", "nice to meet",
      "how are you", "hope you"],
     {"rate": 2, "pitch": "+5Hz", "style": "cheerful"}),

    # Empathetic / Sorry
    (["sorry", "unfortunately", "i apologize", "failed", "error occurred",
      "something went wrong", "couldn't", "unable to", "my apologies",
      "i understand", "that must be"],
     {"rate": 0, "pitch": "-5Hz", "style": "empathetic"}),

    # Hopeful / Reminder
    (["reminder", "don't forget", "upcoming", "tomorrow", "exam",
      "contest", "deadline", "scheduled", "you have", "just a reminder"],
     {"rate": 1, "pitch": "+3Hz", "style": "hopeful"}),

    # Serious / Warning
    (["warning", "danger", "alert", "critical", "important", "attention",
      "be careful", "watch out", "security"],
     {"rate": -1, "pitch": "-8Hz", "style": "serious"}),

    # Curious / Question
    (["did you know", "interesting", "fascinating", "actually", "fun fact",
      "surprisingly", "research shows", "studies"],
     {"rate": 1, "pitch": "+2Hz", "style": "curious"}),

    # Confident / Informational
    (["here are", "i found", "according to", "the result", "system info",
      "cpu", "ram", "memory", "you have", "emails", "reminders"],
     {"rate": 1, "pitch": "0Hz", "style": "confident"}),
]

DEFAULT_EMOTION = {"rate": 1, "pitch": "0Hz", "style": "friendly"}

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
    text = re.sub(r'[⚙*#`•\-_]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:350]

def speak(text: str, emotion: str = None):
    global _speaking

    with _lock:
        if _speaking:
            print("[Voice] Already speaking — skipping")
            return
        _speaking = True

    try:
        clean = clean_text(text)
        if not clean or len(clean) < 3:
            return

        safe = clean.replace("'", " ").replace('"', ' ').replace('\n', ' ')
        emo = detect_emotion(safe)
        rate = emo["rate"]

        print(f"[Voice] Emotion: {emo['style']} | Rate: {rate} | Text: {safe[:40]}...")

        script = f"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice('Microsoft Zira Desktop')
$s.Rate = {rate}
$s.Volume = 100
$s.Speak('{safe}')
$s.Dispose()
"""
        subprocess.run(
            ["powershell", "-WindowStyle", "Hidden", "-Command", script],
            timeout=30,
            capture_output=True
        )
        print(f"[Voice] Done — emotion was '{emo['style']}'")

    except Exception as e:
        print(f"[Voice] Error: {e}")
    finally:
        with _lock:
            _speaking = False

def speak_async(text: str, emotion: str = None):
    threading.Thread(target=speak, args=(text, emotion), daemon=True).start()

def speak_excited(text): speak(text)
def speak_cheerful(text): speak(text)
def speak_sad(text): speak(text)
def speak_calm(text): speak(text)

if __name__ == "__main__":
    print("Testing VERONICA emotional voice...\n")

    tests = [
        "Good morning Pranav! All systems are online and ready for today.",
        "Excellent work! Your task was completed successfully!",
        "I'm sorry, something went wrong. I couldn't complete that request.",
        "Just a reminder — your LeetCode contest is tomorrow at 7:30 AM!",
        "Warning! High CPU usage detected. You should close some applications.",
        "You have 2371 unread emails in your Gmail inbox.",
        "Did you know that LLaMA 3.2 has 1 billion parameters running on your PC?",
    ]

    for t in tests:
        emo = detect_emotion(t)
        print(f"Text: {t[:50]}...")
        print(f"Emotion: {emo['style']} | Rate: {emo['rate']}\n")
        speak(t)
        import time
        time.sleep(0.5)