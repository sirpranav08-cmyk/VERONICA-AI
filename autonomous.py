"""
VERONICA Autonomous Decision Engine
Makes decisions independently based on system state,
time, user patterns, and environmental triggers
"""
import threading
import time
import subprocess
import psutil
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("D:/jarvis-agent/agent/data")
DECISIONS_LOG = DATA_DIR / "decisions_log.json"

# Decision history
decisions = []

# ── NOTIFICATION ──────────────────────────────────────────────────
def notify(title: str, msg: str):
    script = f'''
Add-Type -AssemblyName System.Windows.Forms
$n = New-Object System.Windows.Forms.NotifyIcon
$n.Icon = [System.Drawing.SystemIcons]::Information
$n.Visible = $true
$n.BalloonTipTitle = "{title}"
$n.BalloonTipText = "{msg}"
$n.ShowBalloonTip(5000)
'''
    subprocess.Popen(
        ["powershell", "-WindowStyle", "Hidden", "-Command", script],
        creationflags=subprocess.CREATE_NO_WINDOW
    )

def speak(text: str):
    script = f'''
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice("Microsoft Heera Desktop")
$s.Rate = 0
$s.Speak("{text}")
'''
    subprocess.Popen(
        ["powershell", "-WindowStyle", "Hidden", "-Command", script],
        creationflags=subprocess.CREATE_NO_WINDOW
    )

def log_decision(trigger: str, decision: str, action: str):
    """Log every autonomous decision."""
    entry = {
        "trigger": trigger,
        "decision": decision,
        "action": action,
        "time": datetime.now().isoformat()
    }
    decisions.append(entry)
    if len(decisions) > 500:
        decisions.pop(0)
    try:
        DECISIONS_LOG.write_text(json.dumps(decisions[-50:], indent=2))
    except: pass
    print(f"[Autonomous] Decision: {decision} → {action}")

# ── DECISION: RAM MANAGEMENT ──────────────────────────────────────
last_ram_alert = 0
def check_ram():
    global last_ram_alert
    ram = psutil.virtual_memory()
    now = time.time()

    if ram.percent > 85 and now - last_ram_alert > 300:
        last_ram_alert = now
        # Find and kill heavy non-essential processes
        heavy = []
        for p in psutil.process_iter(['name', 'memory_percent']):
            try:
                if p.info['memory_percent'] > 5:
                    name = p.info['name'].lower()
                    if any(x in name for x in ['chrome', 'msedge', 'discord',
                                                'teams', 'onedrive', 'spotify']):
                        heavy.append(p)
            except: pass

        if heavy:
            killed = []
            for p in heavy[:2]:
                try:
                    name = p.info['name']
                    p.kill()
                    killed.append(name)
                except: pass
            if killed:
                msg = f"RAM at {ram.percent:.0f}%. Closed {', '.join(killed)} to free memory."
                notify("VERONICA — Auto Decision", msg)
                log_decision(f"RAM={ram.percent:.0f}%",
                           "RAM critical — killing heavy apps",
                           f"Killed: {killed}")
        else:
            notify("VERONICA ⚠", f"RAM at {ram.percent:.0f}%. Consider closing apps, Sir.")
            log_decision(f"RAM={ram.percent:.0f}%",
                       "RAM warning",
                       "Notified user")

# ── DECISION: BATTERY MANAGEMENT ─────────────────────────────────
last_battery_alert = 0
last_battery_level = 100
def check_battery():
    global last_battery_alert, last_battery_level
    bat = psutil.sensors_battery()
    if not bat: return

    now = time.time()
    level = bat.percent
    charging = bat.power_plugged

    # Critical battery — dim screen and notify
    if level < 10 and not charging and now - last_battery_alert > 180:
        last_battery_alert = now
        # Dim screen to 20%
        subprocess.run(["powershell", "-Command",
            "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods)"
            ".WmiSetBrightness(1,20)"], capture_output=True)
        notify("VERONICA ⚠ CRITICAL", f"Battery at {level:.0f}%! Please plug in charger!")
        log_decision(f"Battery={level:.0f}%",
                    "Battery critical — dimming screen",
                    "Set brightness 20%, notified")

    # Low battery warning
    elif level < 20 and not charging and now - last_battery_alert > 300:
        last_battery_alert = now
        notify("VERONICA", f"Battery at {level:.0f}%, Sir. Please charge soon.")
        log_decision(f"Battery={level:.0f}%", "Low battery warning", "Notified user")

    # Battery charged — notify
    elif level >= 95 and charging and last_battery_level < 95:
        notify("VERONICA", "Battery fully charged, Sir. You can unplug.")
        log_decision("Battery=95%+", "Battery full", "Notified user")

    last_battery_level = level

# ── DECISION: TIME-BASED AUTOMATION ──────────────────────────────
last_time_decisions = {}
def check_time_decisions():
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    key = f"{hour}:{minute//30}"  # Every 30 min window

    if key in last_time_decisions:
        return
    last_time_decisions[key] = True

    # 7:00 AM — Morning briefing
    if hour == 7 and minute < 30:
        notify("VERONICA — Good Morning",
               "Good morning, Sir! Checking your tasks for today...")
        log_decision("Time=7AM", "Morning routine triggered",
                    "Showing morning briefing")

    # 9:00 AM — Work mode
    elif hour == 9 and minute < 30:
        from veronica_modes import activate_work_mode
        activate_work_mode()
        notify("VERONICA", "Work mode activated automatically, Sir.")
        log_decision("Time=9AM", "Auto work mode", "Activated work mode")

    # 1:00 PM — Lunch reminder
    elif hour == 13 and minute < 30:
        notify("VERONICA", "Sir, it is 1 PM. Time for lunch!")
        log_decision("Time=1PM", "Lunch reminder", "Notified user")

    # 6:00 PM — End of work
    elif hour == 18 and minute < 30:
        notify("VERONICA", "Sir, it is 6 PM. Work day ending. Shall I save your work?")
        log_decision("Time=6PM", "End of work reminder", "Notified user")

    # 10:00 PM — Sleep reminder
    elif hour == 22 and minute < 30:
        notify("VERONICA", "Sir, it is 10 PM. Consider getting rest soon.")
        log_decision("Time=10PM", "Sleep reminder", "Notified user")

    # 11:30 PM — Auto sleep mode
    elif hour == 23 and minute >= 30:
        from veronica_modes import activate_sleep_mode
        activate_sleep_mode()
        log_decision("Time=11:30PM", "Auto sleep mode", "Activated sleep mode")

# ── DECISION: CPU MANAGEMENT ──────────────────────────────────────
last_cpu_alert = 0
def check_cpu():
    global last_cpu_alert
    cpu = psutil.cpu_percent(interval=1)
    now = time.time()

    if cpu > 90 and now - last_cpu_alert > 300:
        last_cpu_alert = now
        # Find CPU hog
        top_proc = None
        top_cpu = 0
        for p in psutil.process_iter(['name', 'cpu_percent']):
            try:
                if p.info['cpu_percent'] > top_cpu:
                    top_cpu = p.info['cpu_percent']
                    top_proc = p.info['name']
            except: pass

        msg = f"CPU at {cpu:.0f}%"
        if top_proc:
            msg += f". {top_proc} is using most CPU."
        notify("VERONICA ⚠", msg + " Performance may be affected, Sir.")
        log_decision(f"CPU={cpu:.0f}%", "High CPU alert",
                    f"Notified — top process: {top_proc}")

# ── DECISION: SCREEN LOCK ─────────────────────────────────────────
last_activity_check = time.time()
IDLE_LOCK_MINUTES = 10

def check_idle():
    """Lock screen if idle too long."""
    try:
        import ctypes
        # Get last input time
        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
        millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
        idle_minutes = millis / 60000

        if idle_minutes > IDLE_LOCK_MINUTES:
            subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
            log_decision(f"Idle={idle_minutes:.0f}min",
                        "Auto lock — user idle too long",
                        "Locked screen")
    except: pass

# ── DECISION: NETWORK MONITOR ─────────────────────────────────────
last_net_check = 0
last_bytes_sent = 0
def check_network():
    global last_net_check, last_bytes_sent
    now = time.time()
    if now - last_net_check < 60:
        return
    last_net_check = now

    net = psutil.net_io_counters()
    if last_bytes_sent > 0:
        sent_mb = (net.bytes_sent - last_bytes_sent) / 1024 / 1024
        if sent_mb > 100:  # More than 100MB sent in 1 minute
            notify("VERONICA ⚠",
                  f"High network upload: {sent_mb:.0f}MB/min. Check for malware, Sir!")
            log_decision(f"Upload={sent_mb:.0f}MB",
                        "High upload detected",
                        "Notified user")
    last_bytes_sent = net.bytes_sent

# ── DECISION: REMINDER AUTO-REMIND ───────────────────────────────
def check_upcoming_reminders():
    """Check if any reminder is coming up in next 30 min."""
    try:
        reminder_file = DATA_DIR / "reminders.json"
        if not reminder_file.exists():
            return
        reminders = json.loads(reminder_file.read_text())
        now = datetime.now()
        for r in reminders:
            if r.get("done"):
                continue
            try:
                target = datetime.fromisoformat(r["datetime"])
                diff = (target - now).total_seconds() / 60
                if 25 <= diff <= 35:  # 30 min warning
                    notify("VERONICA — Reminder",
                          f"Coming up in 30 min: {r['message']}")
                    log_decision("30min reminder",
                               f"Pre-alert: {r['message']}",
                               "Notified user")
            except: pass
    except: pass

# ── MAIN AUTONOMOUS LOOP ──────────────────────────────────────────
def autonomous_loop():
    print("[Autonomous] Decision engine started — VERONICA is now autonomous")
    iteration = 0

    while True:
        try:
            iteration += 1

            # Every 30 seconds
            check_ram()
            check_battery()
            check_cpu()
            check_network()
            check_upcoming_reminders()

            # Every 2 minutes — time decisions
            if iteration % 4 == 0:
                check_time_decisions()

            # Every 10 minutes — idle check
            if iteration % 20 == 0:
                check_idle()

        except Exception as e:
            print(f"[Autonomous] Error: {e}")

        time.sleep(30)

def start():
    t = threading.Thread(target=autonomous_loop, daemon=True)
    t.start()
    print("[Autonomous] VERONICA autonomous mode ON")
    return t

def get_recent_decisions(n: int = 10) -> list:
    return decisions[-n:]