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
    """Use Microsoft Edge Neural TTS — natural female voice."""
    import asyncio
    import edge_tts
    import tempfile
    import subprocess
    import os

    async def _speak():
        # Best female voices:
        # en-US-JennyNeural — warm, friendly
        # en-US-AriaNeural — professional
        # en-IN-NeerjaNeural — Indian English female
        voice = "en-US-JennyNeural"
        communicate = edge_tts.Communicate(text, voice, rate="+5%", pitch="+0Hz")
        tmp = os.path.join(tempfile.gettempdir(), "jarvis_speak.mp3")
        await communicate.save(tmp)
        jarvis_voice.speak(text)
        subprocess.run(
            ["powershell", "-c", f"(New-Object Media.SoundPlayer).PlaySync()"],
            capture_output=True
        )
        # Play using PowerShell
        subprocess.run([
            "powershell", "-WindowStyle", "Hidden", "-Command",
            f"$mp = New-Object System.Windows.Media.MediaPlayer; $mp.Open([uri]'{tmp}'); $mp.Play(); Start-Sleep -Seconds 10"
        ], capture_output=True)

    asyncio.run(_speak())
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