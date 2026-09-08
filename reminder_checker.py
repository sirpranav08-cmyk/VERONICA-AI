import json, time, os, subprocess
from datetime import datetime
from pathlib import Path

REMINDERS_FILE = Path("D:/jarvis-agent/agent/data/reminders.json")

def show_notification(message):
    import jarvis_voice
    jarvis_voice.speak_async(f"Reminder: {message}")
    # Also show popup
    os.system(f'powershell -Command "[System.Reflection.Assembly]::LoadWithPartialName(\'System.Windows.Forms\'); [System.Windows.Forms.MessageBox]::Show(\'{message}\', \'JARVIS Reminder\')"')
def check_reminders():
    print("[Reminder] Checker started")
    while True:
        try:
            if REMINDERS_FILE.exists():
                reminders = json.loads(REMINDERS_FILE.read_text())
                changed = False
                now = datetime.now()
                for r in reminders:
                    if r.get("done"):
                        continue
                    target = datetime.fromisoformat(r["datetime"])
                    if now >= target:
                        msg = r["message"]
                        print(f"[Reminder] FIRED: {msg}")
                        show_notification(msg)
                        # Check if recurring
                        msg = r.get("message", "").lower()
                        if "every" in msg or "weekly" in msg or "daily" in msg:
                        # Reschedule for next week
                            from datetime import timedelta
                            next_dt = target + timedelta(weeks=1)
                            r["datetime"] = next_dt.isoformat()
                            print(f"[Reminder] Rescheduled recurring: {next_dt}")
                        else:
                            r["done"] = True
                        changed = True
                if changed:
                    REMINDERS_FILE.write_text(json.dumps(reminders, indent=2))
        except Exception as e:
            print(f"[Reminder] Error: {e}")
        time.sleep(30)

if __name__ == "__main__":
    check_reminders()
