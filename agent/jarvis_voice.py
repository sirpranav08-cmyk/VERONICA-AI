"""
VERONICA Voice Engine — Simple and reliable
Uses Windows Zira (female) voice directly
"""
import subprocess
import re
import threading

# Track if currently speaking to prevent overlap
_speaking = False
_lock = threading.Lock()

def clean_text(text: str) -> str:
    """Remove URLs, paths, symbols."""
    text = re.sub(r'http[s]?://\S+', '', text)
    text = re.sub(r'[A-Za-z]:\\[\w\\\.\-]+', '', text)
    text = re.sub(r'Executing \w+\.\.\.', '', text)
    text = re.sub(r'[⚙*#`•\-_]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:350]

def detect_emotion(text: str) -> dict:
    """Detect speech rate and pitch from text."""
    lower = text.lower()
    
    if any(w in lower for w in ["good morning", "good afternoon", "hello", "hi", "welcome"]):
        return {"rate": 2, "pitch": "high"}
    
    if any(w in lower for w in ["excellent", "amazing", "great", "congratulations", "perfect"]):
        return {"rate": 3, "pitch": "high"}
    
    if any(w in lower for w in ["sorry", "error", "failed", "unfortunately", "problem"]):
        return {"rate": 0, "pitch": "low"}
    
    if any(w in lower for w in ["reminder", "exam", "tomorrow", "upcoming", "contest"]):
        return {"rate": 1, "pitch": "medium"}
    
    return {"rate": 1, "pitch": "medium"}

def speak(text: str, emotion: str = None):
    """Speak text using Windows Zira voice — one at a time."""
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
        
        # Escape single quotes
        safe = clean.replace("'", " ").replace('"', ' ').replace('\n', ' ')
        
        # Detect emotion for rate
        emo = detect_emotion(safe)
        rate = emo["rate"]
        
        print(f"[Voice] Speaking: {safe[:50]}...")
        
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
        print(f"[Voice] Done speaking")
        
    except Exception as e:
        print(f"[Voice] Error: {e}")
    finally:
        with _lock:
            _speaking = False

def speak_async(text: str, emotion: str = None):
    """Non-blocking speak."""
    threading.Thread(target=speak, args=(text, emotion), daemon=True).start()

# Emotion shortcuts
def speak_cheerful(text): speak(text, "cheerful")
def speak_excited(text): speak(text, "excited")
def speak_sad(text): speak(text, "sad")
def speak_calm(text): speak(text, "calm")

if __name__ == "__main__":
    print("Testing VERONICA voice...")
    speak("Hello Pranav. I am VERONICA, your personal AI assistant. All systems are online and ready.")