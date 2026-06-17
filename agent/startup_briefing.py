"""
JARVIS Startup Briefing
Runs on boot — speaks name, date, time, pending reminders
"""
import json
import subprocess
from datetime import datetime
from pathlib import Path
import jarvis_voice

FACTS_FILE = Path("D:/jarvis-agent/agent/data/facts.json")
REMINDERS_FILE = Path("D:/jarvis-agent/agent/data/reminders.json")

def get_user_name():
    try:
        if FACTS_FILE.exists():
            facts = json.loads(FACTS_FILE.read_text())
            return facts.get("user_name", {}).get("value", "Sir")
    except:
        pass
    return "Sir"

def get_pending_reminders():
    try:
        if REMINDERS_FILE.exists():
            reminders = json.loads(REMINDERS_FILE.read_text())
            now = datetime.now()
            pending = []
            for r in reminders:
                if not r.get("done"):
                    dt = datetime.fromisoformat(r["datetime"])
                    if dt >= now:
                        pending.append((r["message"], dt))
            return pending
    except:
        pass
    return []

def speak(text):
    """Use Windows Zira TTS — fully offline."""
    import subprocess
    safe = text.replace("'", "").replace('"', '').replace('\n', ' ')
    script = f"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice('Microsoft Zira Desktop')
$s.Rate = 1
$s.Volume = 100
$s.Speak('{safe}')
"""
    subprocess.run(
        ["powershell", "-WindowStyle", "Hidden", "-Command", script],
        timeout=60
    )
def build_briefing():
    name = get_user_name()
    now = datetime.now()
    
    # Date and time
    date_str = now.strftime("%A, %B %d %Y")
    time_str = now.strftime("%I:%M %p")
    
    # Greeting
    hour = now.hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    briefing = f"{greeting}, {name}. Today is {date_str}. The time is {time_str}. "

    # Pending reminders
    pending = get_pending_reminders()
    if pending:
        briefing += f"You have {len(pending)} pending task"
        if len(pending) > 1:
            briefing += "s"
        briefing += ". "
        for msg, dt in pending[:3]:  # Max 3
            time_left = dt - now
            days = time_left.days
            if days == 0:
                briefing += f"{msg} is today at {dt.strftime('%I:%M %p')}. "
            elif days == 1:
                briefing += f"{msg} is tomorrow at {dt.strftime('%I:%M %p')}. "
            else:
                briefing += f"{msg} is in {days} days. "
    else:
        briefing += "You have no pending tasks. "

    briefing += "All systems are online. How can I assist you today?"
    return briefing

if __name__ == "__main__":
    print("[Briefing] Starting startup briefing...")
    text = build_briefing()
    print(f"[Briefing] {text}")
    speak(text)
    print("[Briefing] Done.")