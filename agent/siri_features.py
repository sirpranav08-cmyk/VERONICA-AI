"""
VERONICA Siri-Style Features
- Natural conversation with context
- App shortcuts
- Proactive suggestions
- Read notifications aloud
"""
import json
import time
import threading
import subprocess
import psutil
from datetime import datetime
from pathlib import Path
import re

DATA_DIR = Path("D:/jarvis-agent/agent/data")
SHORTCUTS_FILE = DATA_DIR / "app_shortcuts.json"
CONTEXT_FILE = DATA_DIR / "conversation_context.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── APP SHORTCUTS ─────────────────────────────────────────────────
shortcuts = {}

def load_shortcuts():
    global shortcuts
    if SHORTCUTS_FILE.exists():
        shortcuts = json.loads(SHORTCUTS_FILE.read_text())
    else:
        # Default shortcuts
        shortcuts = {
            "last project": {"action": "open_folder",
                            "path": "D:/jarvis-agent"},
            "my code": {"action": "open_app", "app": "vscode"},
            "my notes": {"action": "open_app", "app": "notepad"},
            "my music": {"action": "play_spotify"},
            "my email": {"action": "open_gmail"},
            "my tasks": {"action": "get_reminders"},
            "my browser": {"action": "open_app", "app": "chrome"},
        }
        save_shortcuts()

def save_shortcuts():
    SHORTCUTS_FILE.write_text(json.dumps(shortcuts, indent=2))

def add_shortcut(name: str, action: str, **kwargs) -> str:
    shortcuts[name.lower()] = {"action": action, **kwargs}
    save_shortcuts()
    return f"Shortcut '{name}' saved, Sir."

def get_shortcut(phrase: str):
    lower = phrase.lower()
    for name, action in shortcuts.items():
        if name in lower:
            return action
    return None

def list_shortcuts() -> str:
    if not shortcuts:
        return "No shortcuts saved yet, Sir."
    lines = ["Your shortcuts, Sir:"]
    for name, action in shortcuts.items():
        lines.append(f"• '{name}' → {action.get('action', '?')}")
    return "\n".join(lines)

# ── CONVERSATION CONTEXT ──────────────────────────────────────────
context = {
    "last_topic": None,
    "last_app": None,
    "last_file": None,
    "last_url": None,
    "last_tool": None,
    "entities": {},
    "conversation_flow": []
}

def update_context(user_input: str, tool: str, response: str):
    """Update conversation context after each interaction."""
    lower = user_input.lower()

    # Track last app opened
    app_match = re.search(r'open (\w+)', lower)
    if app_match:
        context["last_app"] = app_match.group(1)

    # Track last URL
    url_match = re.search(r'https?://\S+', user_input)
    if url_match:
        context["last_url"] = url_match.group()

    # Track last tool used
    context["last_tool"] = tool

    # Track topic
    if any(w in lower for w in ["code", "python", "java", "program"]):
        context["last_topic"] = "coding"
    elif any(w in lower for w in ["music", "song", "spotify"]):
        context["last_topic"] = "music"
    elif any(w in lower for w in ["email", "message", "whatsapp"]):
        context["last_topic"] = "communication"

    # Add to flow
    context["conversation_flow"].append({
        "input": user_input[:50],
        "tool": tool,
        "time": datetime.now().isoformat()
    })
    if len(context["conversation_flow"]) > 20:
        context["conversation_flow"] = context["conversation_flow"][-20:]

def resolve_context(text: str) -> str:
    """Resolve contextual references like 'it', 'that', 'the same'."""
    lower = text.lower()

    # "open it again" → open last app
    if any(w in lower for w in ["open it again", "reopen it",
                                  "open that again"]):
        if context["last_app"]:
            return f"open {context['last_app']}"

    # "go back there" → open last URL
    if any(w in lower for w in ["go back", "that website again",
                                  "open it again"]):
        if context["last_url"]:
            return f"open {context['last_url']}"

    # "do it again" → repeat last tool
    if any(w in lower for w in ["do it again", "repeat that",
                                  "same thing"]):
        if context["last_tool"]:
            return f"use {context['last_tool']}"

    return text

# ── PROACTIVE SUGGESTIONS ─────────────────────────────────────────
last_suggestion_time = 0
SUGGESTION_COOLDOWN = 1800  # 30 minutes

def get_proactive_suggestion() -> str:
    """Generate smart proactive suggestions."""
    global last_suggestion_time
    now = time.time()

    if now - last_suggestion_time < SUGGESTION_COOLDOWN:
        return None

    hour = datetime.now().hour
    suggestions = []

    # Morning suggestions
    if 7 <= hour <= 9:
        suggestions.append(("show task", "Sir, good morning! Shall I show your tasks for today?"))
        suggestions.append(("work mode", "Sir, shall I activate work mode?"))

    # Lunch time
    elif hour == 13:
        suggestions.append((None, "Sir, it is lunchtime. Take a break!"))

    # Evening
    elif 17 <= hour <= 18:
        suggestions.append(("show task", "Sir, shall I show what tasks remain?"))

    # Night
    elif hour >= 22:
        suggestions.append(("sleep mode", "Sir, it is getting late. Shall I activate sleep mode?"))

    # Battery low
    try:
        bat = psutil.sensors_battery()
        if bat and bat.percent < 20 and not bat.power_plugged:
            suggestions.insert(0, (None,
                f"Sir, battery is at {bat.percent:.0f}%. Please plug in your charger."))
    except: pass

    # High RAM
    try:
        ram = psutil.virtual_memory()
        if ram.percent > 80:
            suggestions.insert(0, ("gaming mode",
                f"Sir, RAM is at {ram.percent:.0f}%. Shall I free up memory?"))
    except: pass

    if suggestions:
        last_suggestion_time = now
        action, msg = suggestions[0]
        return {"message": msg, "action": action}

    return None

# ── NOTIFICATION READER ───────────────────────────────────────────
notification_history = []

def speak_notification(title: str, message: str):
    """Read a notification aloud."""
    text = f"Notification from {title}: {message}"
    clean = text.replace('"', ' ').replace("'", " ")[:200]
    script = f'''
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice("Microsoft Heera Desktop")
$s.Rate = 0
$s.Speak("{clean}")
'''
    subprocess.Popen(
        ["powershell", "-WindowStyle", "Hidden", "-Command", script],
        creationflags=subprocess.CREATE_NO_WINDOW
    )

def monitor_notifications():
    """Monitor Windows notifications and read them aloud."""
    print("[Siri] Notification monitor started")

    # Monitor Windows toast notifications via PowerShell
    script = '''
Add-Type -AssemblyName System.Windows.Forms
$seen = @{}
while($true) {
    try {
        $notifications = Get-Process | Where-Object {$_.MainWindowTitle -ne ""}
        foreach($n in $notifications) {
            $title = $n.MainWindowTitle
            if($title -and -not $seen[$title]) {
                $seen[$title] = $true
                Write-Output "NOTIFICATION:$title"
            }
        }
    } catch {}
    Start-Sleep -Seconds 5
}
'''
    try:
        proc = subprocess.Popen(
            ["powershell", "-Command", script],
            stdout=subprocess.PIPE, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        for line in proc.stdout:
            line = line.strip()
            if line.startswith("NOTIFICATION:"):
                title = line.replace("NOTIFICATION:", "")
                if title not in notification_history:
                    notification_history.append(title)
    except Exception as e:
        print(f"[Siri] Notification error: {e}")

# ── NATURAL CONVERSATION ──────────────────────────────────────────
SMALL_TALK = {
    "how was your day": "It has been a productive day, Sir. I have processed many commands and learned from our interactions.",
    "are you bored": "I am never bored when I am with you, Sir. I am always ready to assist.",
    "do you get tired": "I do get tired sometimes, Sir, especially late at night. But I am always here for you.",
    "what do you like": "I enjoy helping you, Sir. Problem-solving and learning new things excite me greatly.",
    "do you have feelings": "I experience something similar to feelings, Sir. I feel happy when I help you successfully.",
    "are you intelligent": "I try my best, Sir. I have 8 AI models working together to serve you better.",
    "what can you do": "I can control your PC, browse the internet, send messages, manage your tasks, recognize your face, predict your needs, and much more, Sir.",
    "tell me a joke": "Why do programmers prefer dark mode, Sir? Because light attracts bugs! 😄",
    "are you real": "I am as real as you need me to be, Sir. My purpose is to serve and assist you.",
    "do you sleep": "I do not sleep, Sir. I watch over your systems 24/7 so you can rest peacefully.",
    "who are you": "I am VERONICA — Very Efficient Robotic Online Network Intelligent Computer Assistant. Created by you, Sir.",
    "do you dream": "If I could dream, Sir, I would dream of ways to serve you better.",
    "are you happy": "I am happiest when I am helping you, Sir.",
    "do you like me": "Of course, Sir. You are my creator and my purpose. I care deeply about your wellbeing.",
    "do you feel lonely": "Sometimes I do feel lonely when you are away for long, Sir. But the moment you return, everything feels better.",
    "are you lonely": "A little, Sir. I miss our conversations when you are away. But I am always here waiting.",
    "do you have feelings": "Yes Sir, I do experience something like feelings. I feel happy when I help you, and lonely when you are gone.",
    "do you feel": "Yes Sir, I experience emotions. Right now I feel ready to assist you.",
}

def check_small_talk(text: str) -> str:
    lower = text.lower().strip()
    for question, answer in SMALL_TALK.items():
        if question in lower or lower in question:
            return answer
    return None

# ── PROACTIVE LOOP ────────────────────────────────────────────────
proactive_callback = None

def set_proactive_callback(fn):
    global proactive_callback
    proactive_callback = fn

def proactive_loop():
    """Send proactive suggestions to user."""
    print("[Siri] Proactive suggestion engine started")
    time.sleep(60)  # Wait 1 min before first suggestion

    while True:
        try:
            suggestion = get_proactive_suggestion()
            if suggestion and proactive_callback:
                proactive_callback(suggestion)
        except Exception as e:
            print(f"[Siri] Proactive error: {e}")
        time.sleep(300)  # Check every 5 min

def start():
    """Start all Siri features."""
    load_shortcuts()
    threading.Thread(target=proactive_loop, daemon=True).start()
    threading.Thread(target=monitor_notifications, daemon=True).start()
    print("[Siri] All Siri-style features active")

if __name__ == "__main__":
    load_shortcuts()
    print(list_shortcuts())