# -*- coding: utf-8 -*-
"""
VERONICA Activity Monitor
Monitors all user activities on the PC:
- Active window/app tracking
- Keyboard & mouse activity
- Website visits
- File operations
- Screen time per app
- Productivity scoring
- Daily reports
"""
from email.mime import text
from itertools import cycle
import json
import time
import threading
import subprocess
import psutil
import os
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# ── Storage ───────────────────────────────────────────────────────
MONITOR_DIR = Path("D:/jarvis-agent/agent/data/activity")
MONITOR_DIR.mkdir(parents=True, exist_ok=True)

ACTIVITY_LOG  = MONITOR_DIR / "activity_log.json"
APP_USAGE     = MONITOR_DIR / "app_usage.json"
DAILY_REPORT  = MONITOR_DIR / "daily_report.json"
PRODUCTIVITY  = MONITOR_DIR / "productivity.json"

# ── App categories ────────────────────────────────────────────────
APP_CATEGORIES = {
    # Productive
    "productive": [
        "code", "vscode", "pycharm", "intellij", "notepad",
        "word", "excel", "powerpoint", "sublime", "atom",
        "terminal", "cmd", "powershell", "python", "node",
        "github", "gitlab", "stackoverflow", "leetcode",
        "coursera", "udemy", "khan", "notion", "obsidian"
    ],
    # Communication
    "communication": [
        "outlook", "gmail", "teams", "slack", "zoom",
        "meet", "discord", "whatsapp", "telegram"
    ],
    # Entertainment
    "entertainment": [
        "youtube", "netflix", "spotify", "vlc", "steam",
        "epic", "game", "twitch", "prime video", "hotstar"
    ],
    # Social media
    "social": [
        "instagram", "twitter", "facebook", "tiktok",
        "reddit", "linkedin", "snapchat"
    ],
    # Browser
    "browser": [
        "chrome", "firefox", "edge", "opera", "brave"
    ]
}
# ── App limits (minutes per day) ─────────────────────────────────
APP_LIMITS = {
    "youtube": 30,
    "chrome": 60,    # when used for entertainment
    "netflix": 60,
    "spotify": 120,
    "steam": 60,
    "epic": 60,
    "instagram": 20,
    "twitter": 20,
    "facebook": 20,
    "reddit": 20,
    "tiktok": 15,
    "vlc": 60,
    "discord": 45,
}

# ── Apps to block completely ──────────────────────────────────────
BLOCKED_APPS = []  # Add app names here to block completely

class ActivityMonitor:
    def __init__(self):
        self.running = False
        self.current_app = ""
        self.current_window = ""
        self.app_start_time = datetime.now()
        self.session_start = datetime.now()

        # Load existing data
        self.app_usage = self._load(APP_USAGE, {})
        self.activity_log = self._load(ACTIVITY_LOG, [])
        self.productivity_scores = self._load(PRODUCTIVITY, [])

        # Real-time tracking
        self.keystroke_count = 0
        self.mouse_clicks = 0
        self.idle_seconds = 0
        self._warned = set()  # Track already-warned apps
        self.last_activity = time.time()

        print("[Monitor] Activity monitor initialized")

    def _load(self, path: Path, default):
        if path.exists():
            try:
                return json.loads(path.read_text(encoding='utf-8'))
            except:
                pass
        return default

    def _save(self, path: Path, data):
        try:
            path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
        except Exception as e:
            print(f"[Monitor] Save error: {e}")

    # ── Active window detection ───────────────────────────────────
    def get_active_window(self) -> tuple:
        try:
            result = subprocess.run([
                "powershell", "-Command",
                "Add-Type @'\n"
                "using System;\n"
                "using System.Runtime.InteropServices;\n"
                "using System.Text;\n"
                "public class WinAPI {\n"
                "    [DllImport(\"user32.dll\")] public static extern IntPtr GetForegroundWindow();\n"
                "    [DllImport(\"user32.dll\")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int c);\n"
                "    [DllImport(\"user32.dll\")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint p);\n"
                "}\n"
                "'@\n"
                "$h = [WinAPI]::GetForegroundWindow();\n"
                "$s = New-Object System.Text.StringBuilder 256;\n"
                "[WinAPI]::GetWindowText($h, $s, 256) | Out-Null;\n"
                "$s.ToString()"
            ], capture_output=True, text=True, timeout=2)
            title = result.stdout.strip()
        except:
            title = ""

        # Get active process
        try:
            for proc in psutil.process_iter(['name', 'status']):
                if proc.info['status'] == 'running':
                    return proc.info['name'].lower(), title
        except:
            pass
        return "", title

    def get_active_app_simple(self) -> str:
        """Simpler method using tasklist."""
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-Process | Where-Object {$_.MainWindowHandle -ne 0} | "
                 "Select-Object -First 1 -ExpandProperty Name"],
                capture_output=True, text=True, timeout=3
            )
            return result.stdout.strip().lower()
        except:
            return ""

    def categorize_app(self, app_name: str, window_title: str = "") -> str:
        """Categorize an app as productive/entertainment/etc."""
        combined = f"{app_name} {window_title}".lower()
        for category, keywords in APP_CATEGORIES.items():
            if any(k in combined for k in keywords):
                return category
        return "other"

    # ── Tracking ──────────────────────────────────────────────────
    def track_app_time(self):
        """Track time spent in each app."""
        app = self.get_active_app_simple()
        now = datetime.now()

        if app and app != self.current_app:
            # Save previous app session
            if self.current_app:
                duration = (now - self.app_start_time).seconds
                if duration > 5:  # Only log if > 5 seconds
                    date_key = now.strftime("%Y-%m-%d")
                    if date_key not in self.app_usage:
                        self.app_usage[date_key] = {}
                    if self.current_app not in self.app_usage[date_key]:
                        self.app_usage[date_key][self.current_app] = 0
                    self.app_usage[date_key][self.current_app] += duration

            self.current_app = app
            self.app_start_time = now

    def log_activity(self, activity_type: str, details: str):
        """Log a specific activity."""
        entry = {
            "type": activity_type,
            "details": details[:200],
            "app": self.current_app,
            "time": datetime.now().isoformat()
        }
        self.activity_log.append(entry)
        if len(self.activity_log) > 5000:
            self.activity_log = self.activity_log[-5000:]

    # ── Keyboard monitoring ───────────────────────────────────────
    def start_keyboard_monitor(self):
        """Monitor keyboard activity."""
        try:
            import keyboard
            keyboard.on_press(self._on_key)
            print("[Monitor] Keyboard monitoring active")
        except ImportError:
            print("[Monitor] Install 'keyboard' package for keyboard monitoring")
        except Exception as e:
            print(f"[Monitor] Keyboard monitor error: {e}")

    def _on_key(self, event):
        self.keystroke_count += 1
        self.last_activity = time.time()

    # ── Mouse monitoring ──────────────────────────────────────────
    def start_mouse_monitor(self):
        """Monitor mouse activity."""
        try:
            import mouse
            mouse.on_click(self._on_click)
            print("[Monitor] Mouse monitoring active")
        except ImportError:
            print("[Monitor] Install 'mouse' package for mouse monitoring")
        except Exception as e:
            print(f"[Monitor] Mouse monitor error: {e}")

    def _on_click(self):
        self.mouse_clicks += 1
        self.last_activity = time.time()

    # ── Idle detection ────────────────────────────────────────────
    def check_idle(self):
        idle = time.time() - self.last_activity
        if idle > 300:  # 5 minutes idle
            self.idle_seconds += 30
            return True
        return False
    def check_app_limits(self):
        """Check if any app has exceeded its daily limit."""
        today = datetime.now().strftime("%Y-%m-%d")
        today_usage = self.app_usage.get(today, {})

        for app, limit_mins in APP_LIMITS.items():
            # Find matching app in usage
            for used_app, duration in today_usage.items():
                if app in used_app.lower():
                    used_mins = duration // 60
                    limit_secs = limit_mins * 60
                    remaining_mins = limit_mins - used_mins

                    # Warn at 80% of limit
                    if duration >= limit_secs * 0.8 and duration < limit_secs:
                        warn_key = f"warn_{app}_{today}"
                        if warn_key not in self._warned:
                            self._warned.add(warn_key)
                            self._speak_alert(
                                f"Sir, you have been using {app} for {used_mins} minutes. "
                                f"Your limit is {limit_mins} minutes. "
                                f"Only {remaining_mins} minutes remaining."
                            )
                            self._notify_alert(
                                f"VERONICA — {app.title()} Warning",
                                f"{used_mins}/{limit_mins} minutes used. {remaining_mins} mins left!"
                            )

                    # Close and block at limit
                    elif duration >= limit_secs:
                        block_key = f"block_{app}_{today}"
                        if block_key not in self._warned:
                            self._warned.add(block_key)
                            self._close_app(used_app)
                            self._speak_alert(
                                f"Sir, you have reached your daily limit for {app}. "
                                f"I am closing it now. "
                                f"You have used it for {used_mins} minutes today. "
                                f"Time to focus on productive work, Sir!"
                            )
                            self._notify_alert(
                                f"VERONICA — {app.title()} Blocked!",
                                f"Daily limit of {limit_mins} minutes reached! App closed."
                            )

        # Check blocked apps
        for blocked in BLOCKED_APPS:
            if blocked.lower() in self.current_app.lower():
                self._close_app(self.current_app)
                self._speak_alert(
                    f"Sir, {blocked} is on your blocked list. Closing it now."
                )

    def _close_app(self, app_name: str):
        """Force close an application."""
        # Try taskkill
        subprocess.run(
            ["taskkill", "/f", "/im", f"{app_name}.exe"],
            capture_output=True
        )
        # Also try closing browser tabs
        if any(b in app_name.lower() for b in ["chrome","edge","firefox"]):
            subprocess.run(
                ["taskkill", "/f", "/im", f"{app_name}.exe"],
                capture_output=True
            )
        self.log_activity("app_blocked", f"Closed {app_name} — limit reached")

    def _speak_alert(self, text: str):
        """Speak an alert message."""
        safe = text.replace("'", " ").replace('"', ' ')[:300]
        subprocess.Popen([
            "powershell", "-WindowStyle", "Hidden", "-Command",
            f"Add-Type -AssemblyName System.Speech;"
            f"$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
            f"$s.SelectVoice('Microsoft Zira Desktop');"
            f"$s.Rate = 2; $s.Speak('{safe}')"
        ], creationflags=subprocess.CREATE_NO_WINDOW)

    def _notify_alert(self, title: str, msg: str):
        """Show notification popup."""
        subprocess.Popen([
        "powershell", "-WindowStyle", "Hidden", "-Command",
        f'Add-Type -AssemblyName System.Windows.Forms;'
        f'$n = New-Object System.Windows.Forms.NotifyIcon;'
        f'$n.Icon = [System.Drawing.SystemIcons]::Warning;'
        f'$n.Visible = $true;'
        f'$n.BalloonTipTitle = "{title}";'
        f'$n.BalloonTipText = "{msg}";'
        f'$n.ShowBalloonTip(6000)'
        ], creationflags=subprocess.CREATE_NO_WINDOW)

    # ── Productivity scoring ──────────────────────────────────────
    def calculate_productivity(self) -> float:
        """Calculate productivity score 0-100."""
        today = datetime.now().strftime("%Y-%m-%d")
        today_usage = self.app_usage.get(today, {})

        if not today_usage:
            return 0.0

        total_time = sum(today_usage.values())
        if total_time == 0:
            return 0.0

        productive_time = 0
        for app, duration in today_usage.items():
            category = self.categorize_app(app)
            if category == "productive":
                productive_time += duration
            elif category == "communication":
                productive_time += duration * 0.5

        score = (productive_time / total_time) * 100
        return min(100.0, score)

    # ── Reports ───────────────────────────────────────────────────
    def get_today_summary(self) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        today_usage = self.app_usage.get(today, {})
        session_mins = (datetime.now() - self.session_start).seconds // 60

        if not today_usage:
            return (f"No activity recorded today, Sir.\n"
                    f"Current session: {session_mins} minutes")

        # Sort by time
        sorted_apps = sorted(today_usage.items(),
                             key=lambda x: x[1], reverse=True)
        total = sum(today_usage.values())
        productivity = self.calculate_productivity()

        lines = [
            f"Today's Activity Summary, Sir:",
            f"Total screen time: {total//3600}h {(total%3600)//60}m",
            f"Productivity score: {productivity:.0f}%",
            f"Keystrokes: {self.keystroke_count}",
            f"Mouse clicks: {self.mouse_clicks}",
            f"",
            f"Top apps:"
        ]

        for app, duration in sorted_apps[:8]:
            mins = duration // 60
            secs = duration % 60
            category = self.categorize_app(app)
            lines.append(f"  - {app}: {mins}m {secs}s [{category}]")

        return "\n".join(lines)

    def get_app_breakdown(self) -> str:
        """Get breakdown by category."""
        today = datetime.now().strftime("%Y-%m-%d")
        today_usage = self.app_usage.get(today, {})

        if not today_usage:
            return "No app usage data today, Sir."

        category_time = defaultdict(int)
        for app, duration in today_usage.items():
            cat = self.categorize_app(app)
            category_time[cat] += duration

        total = sum(category_time.values())
        lines = ["App category breakdown, Sir:"]
        for cat, duration in sorted(category_time.items(),
                                    key=lambda x: x[1], reverse=True):
            pct = (duration / total * 100) if total > 0 else 0
            mins = duration // 60
            lines.append(f"  - {cat}: {mins}m ({pct:.0f}%)")

        return "\n".join(lines)

    def get_productivity_insight(self) -> str:
        """Get AI-style productivity insight."""
        score = self.calculate_productivity()
        today = datetime.now().strftime("%Y-%m-%d")
        today_usage = self.app_usage.get(today, {})
        total = sum(today_usage.values()) if today_usage else 0
        hours = total // 3600

        if score >= 80:
            msg = (f"Excellent productivity today, Sir! "
                   f"Score: {score:.0f}%. "
                   f"You have been highly focused for {hours} hours.")
        elif score >= 60:
            msg = (f"Good productivity today, Sir. "
                   f"Score: {score:.0f}%. "
                   f"Consider reducing entertainment time.")
        elif score >= 40:
            msg = (f"Moderate productivity, Sir. "
                   f"Score: {score:.0f}%. "
                   f"Try focusing more on coding and studying.")
        else:
            msg = (f"Low productivity today, Sir. "
                   f"Score: {score:.0f}%. "
                   f"Consider activating Study Mode.")

        return msg

    def generate_daily_report(self) -> dict:
        """Generate full daily report."""
        today = datetime.now().strftime("%Y-%m-%d")
        today_usage = self.app_usage.get(today, {})

        report = {
            "date": today,
            "total_screen_time_mins": sum(today_usage.values()) // 60,
            "productivity_score": self.calculate_productivity(),
            "keystrokes": self.keystroke_count,
            "mouse_clicks": self.mouse_clicks,
            "top_apps": dict(sorted(today_usage.items(),
                                   key=lambda x: x[1], reverse=True)[:10]),
            "idle_time_mins": self.idle_seconds // 60,
            "generated_at": datetime.now().isoformat()
        }

        # Save report
        reports = self._load(DAILY_REPORT, [])
        reports.append(report)
        if len(reports) > 30:
            reports = reports[-30:]
        self._save(DAILY_REPORT, reports)

        return report

    # ── Main monitoring loop ──────────────────────────────────────
    def run(self):
        self.running = True
        print("[Monitor] Activity monitoring started")
        cycle = 0

        # Start input monitors
        threading.Thread(target=self.start_keyboard_monitor, daemon=True).start()
        threading.Thread(target=self.start_mouse_monitor, daemon=True).start()

        while self.running:
            try:
                cycle += 1

                # Track app every 5 seconds
                self.track_app_time()
                # Check app limits every 30 seconds
                if cycle % 6 == 0:
                    self.check_app_limits()

                # Check idle
                self.check_idle()

                # Save data every minute
                if cycle % 12 == 0:
                    self._save(APP_USAGE, self.app_usage)
                    self._save(ACTIVITY_LOG, self.activity_log)

                # Generate daily report at midnight
                now = datetime.now()
                if now.hour == 0 and now.minute == 0:
                    self.generate_daily_report()
                    # Reset daily counters
                    self.keystroke_count = 0
                    self.mouse_clicks = 0
                    self.idle_seconds = 0
                    self._warned = set()  # Track already-warned apps

                time.sleep(5)

            except Exception as e:
                print(f"[Monitor] Error: {e}")
                time.sleep(10)

    def stop(self):
        self.running = False
        self._save(APP_USAGE, self.app_usage)
        print("[Monitor] Activity monitor stopped")

# ── Global instance ───────────────────────────────────────────────
_monitor = None

def get_monitor() -> ActivityMonitor:
    global _monitor
    if _monitor is None:
        _monitor = ActivityMonitor()
    return _monitor

def start_monitoring():
    monitor = get_monitor()
    t = threading.Thread(target=monitor.run, daemon=True)
    t.start()
    print("[Monitor] Background monitoring started")
    return monitor

def get_activity_summary() -> str:
    return get_monitor().get_today_summary()

def get_productivity_score() -> str:
    monitor = get_monitor()
    score = monitor.calculate_productivity()
    return monitor.get_productivity_insight()

def get_app_breakdown() -> str:
    return get_monitor().get_app_breakdown()

if __name__ == "__main__":
    print("Testing activity monitor...")
    monitor = ActivityMonitor()
    print(monitor.get_today_summary())
    print(monitor.get_productivity_insight())