# -*- coding: utf-8 -*-
"""
VERONICA Modes - Study, Work, Gaming, Sleep, Presentation
Full laptop control through mode switching
"""
import subprocess
import os
import time
import threading

def set_volume(level: int):
    """Set system volume 0-100."""
    subprocess.run(["powershell", "-WindowStyle", "Hidden", "-Command",
        f"$obj = New-Object -ComObject WScript.Shell;"
        f"for($i=0;$i -lt 50;$i++){{$obj.SendKeys([char]174)}};"
        f"for($i=0;$i -lt {level//2};$i++){{$obj.SendKeys([char]175)}}"],
        capture_output=True)

def notify(title, msg):
    """Show Windows notification."""
    subprocess.Popen(["powershell", "-WindowStyle", "Hidden", "-Command",
        f'Add-Type -AssemblyName System.Windows.Forms;'
        f'$n = New-Object System.Windows.Forms.NotifyIcon;'
        f'$n.Icon = [System.Drawing.SystemIcons]::Information;'
        f'$n.Visible = $true;'
        f'$n.BalloonTipTitle = "{title}";'
        f'$n.BalloonTipText = "{msg}";'
        f'$n.ShowBalloonTip(4000)'],
        creationflags=subprocess.CREATE_NO_WINDOW)

def kill_apps(*names):
    """Kill multiple apps by name."""
    for name in names:
        subprocess.run(["taskkill", "/f", "/im", name], capture_output=True)

def set_power_plan(plan: str):
    """Set power plan: balanced, performance."""
    plans = {
        "balanced": "381b4222-f694-41f0-9685-ff5bb260df2e",
        "performance": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
        "saver": "a1841308-3541-4fab-bc81-f71556f20b4a",
    }
    guid = plans.get(plan, plans["balanced"])
    subprocess.run(["powercfg", "/setactive", guid], capture_output=True)

def toggle_notifications(enable: bool):
    """Enable or disable Windows toast notifications."""
    val = 1 if enable else 0
    subprocess.run(["powershell", "-Command",
        f"Set-ItemProperty -Path "
        f"'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\PushNotifications' "
        f"-Name ToastEnabled -Value {val}"],
        capture_output=True)

# ── STUDY MODE ────────────────────────────────────────────────────
def activate_study_mode() -> str:
    kill_apps("Spotify.exe", "discord.exe", "WhatsApp.exe",
              "steam.exe", "EpicGamesLauncher.exe")
    set_volume(30)
    set_power_plan("balanced")
    toggle_notifications(False)
    subprocess.Popen(["notepad.exe"])
    notify("VERONICA - Study Mode",
           "Focus mode active. Distractions closed. Stay focused, Sir!")
    return ("Study Mode activated, Sir. "
            "Distracting apps closed, volume set to 30 percent, "
            "Notepad opened for notes. Stay focused!")

# ── WORK MODE ─────────────────────────────────────────────────────
def activate_work_mode() -> str:
    subprocess.Popen(["start", "chrome",
                      "--new-window", "https://gmail.com"],
                     shell=True)
    set_volume(50)
    set_power_plan("performance")
    toggle_notifications(True)
    notify("VERONICA - Work Mode",
           "Work mode active. Gmail opened. Let's go, Sir!")
    return ("Work Mode activated, Sir. "
            "Gmail opened, volume set to 50 percent, "
            "high performance power plan enabled.")

# ── GAMING MODE ───────────────────────────────────────────────────
def activate_gaming_mode() -> str:
    kill_apps("chrome.exe", "msedge.exe", "notepad.exe",
              "OneDrive.exe", "SearchApp.exe")
    set_volume(70)
    set_power_plan("performance")
    toggle_notifications(False)
    notify("VERONICA - Gaming Mode",
           "Gaming mode active. RAM cleared, performance maximized!")
    return ("Gaming Mode activated, Sir. "
            "Background apps closed to free RAM, "
            "volume set to 70 percent, high performance enabled. "
            "Have a great game, Sir!")

# ── SLEEP MODE ────────────────────────────────────────────────────
def activate_sleep_mode() -> str:
    set_volume(0)
    notify("VERONICA - Sleep Mode", "Good night, Sir. Sleep well!")
    def sleep_after():
        time.sleep(3)
        subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
        time.sleep(2)
        subprocess.run(["powershell", "-Command",
            "Add-Type -Assembly System.Windows.Forms;"
            "[System.Windows.Forms.Application]::SetSuspendState("
            "'Suspend', $false, $false)"],
            capture_output=True)
    threading.Thread(target=sleep_after, daemon=True).start()
    return "Sleep mode activated, Sir. Good night!"

# ── PRESENTATION MODE ─────────────────────────────────────────────
def activate_presentation_mode() -> str:
    toggle_notifications(False)
    set_volume(60)
    set_power_plan("performance")
    notify("VERONICA - Presentation Mode",
           "Presentation mode active. Notifications disabled, Sir!")
    return ("Presentation Mode activated, Sir. "
            "Notifications disabled, performance maximized. "
            "Good luck with your presentation!")

# ── NIGHT MODE ────────────────────────────────────────────────────
def activate_night_mode() -> str:
    set_volume(20)
    subprocess.run(["powershell", "-Command",
        "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods)"
        ".WmiSetBrightness(1, 20)"],
        capture_output=True)
    toggle_notifications(False)
    notify("VERONICA - Night Mode", "Night mode active. Brightness reduced, Sir!")
    return ("Night Mode activated, Sir. "
            "Brightness reduced to 20 percent, volume lowered, "
            "notifications disabled.")
# ── PERFORMANCE MODE ──────────────────────────────────────────────
def activate_performance_mode() -> str:
    import json
    from pathlib import Path

    # Set high performance power plan
    set_power_plan("performance")

    # Kill background apps to free RAM
    kill_apps("chrome.exe", "msedge.exe", "OneDrive.exe",
              "SearchApp.exe", "SearchIndexer.exe")

    # Set volume to 70%
    set_volume(70)

    # Switch to most powerful available model
    config_file = Path("D:/jarvis-agent/agent/core/config.py")
    content = config_file.read_text(encoding="utf-8")

    # Check which models are available via ollama
    result = subprocess.run(
        ["ollama", "list"],
        capture_output=True, text=True
    )
    ollama_output = result.stdout.lower()

    # Pick best available model
    best_model = "llama3.2:1b"  # default
    if "llama3.2:latest" in ollama_output or "llama3.2" in ollama_output:
        best_model = "llama3.2"
    if "mistral" in ollama_output:
        best_model = "mistral"
    if "phi3" in ollama_output:
        best_model = "phi3:mini"

    # Update config.py model
    import re
    new_content = re.sub(
        r'model: str = "[^"]*"',
        f'model: str = "{best_model}"',
        content
    )
    config_file.write_text(new_content, encoding="utf-8")

    notify("VERONICA - Performance Mode",
           f"Performance mode active! Switched to {best_model}, Sir!")

    return (f"Performance Mode activated, Sir. "
            f"Switched to {best_model} model, "
            f"background apps closed, "
            f"high performance power plan enabled. "
            f"Please restart the agent for model change to take effect.")
# ── FAST MODE ─────────────────────────────────────────────────────
def activate_fast_mode() -> str:
    import re
    from pathlib import Path

    config_file = Path("D:/jarvis-agent/agent/core/config.py")
    content = config_file.read_text(encoding="utf-8")

    # Switch to tinyllama for fastest responses
    new_content = re.sub(
        r'model: str = "[^"]*"',
        'model: str = "tinyllama"',
        content
    )
    # Also reduce context for speed
    new_content = re.sub(
        r'max_short_term: int = \d+',
        'max_short_term: int = 3',
        new_content
    )
    new_content = re.sub(
        r'temperature: float = [\d\.]+',
        'temperature: float = 0.1',
        new_content
    )
    config_file.write_text(new_content, encoding="utf-8")

    notify("VERONICA - Fast Mode",
           "Fast mode active! Using TinyLlama for instant responses, Sir!")

    return ("Fast Mode activated, Sir. "
            "Switched to TinyLlama — responses will be near instant. "
            "Please restart the agent to apply changes.")
# ── PERFORMANCE MODE ──────────────────────────────────────────────
def activate_performance_mode() -> str:
    import json
    from pathlib import Path

    # Set high performance power plan
    set_power_plan("performance")

    # Kill background apps to free RAM
    kill_apps("chrome.exe", "msedge.exe", "OneDrive.exe",
              "SearchApp.exe", "SearchIndexer.exe")

    # Set volume to 50%
    set_volume(50)

    # Switch to most powerful available model
    config_file = Path("D:/jarvis-agent/agent/core/config.py")
    content = config_file.read_text(encoding="utf-8")

    # Check which models are available via ollama
    result = subprocess.run(
        ["ollama", "list"],
        capture_output=True, text=True
    )
    ollama_output = result.stdout.lower()

    # Pick best available model
    best_model = "llama3.2:1b"  # default
    if "llama3.2:latest" in ollama_output or "llama3.2" in ollama_output:
        best_model = "llama3.2"
    if "mistral" in ollama_output:
        best_model = "mistral"
    if "phi3" in ollama_output:
        best_model = "phi3:mini"

    # Update config.py model
    import re
    new_content = re.sub(
        r'model: str = "[^"]*"',
        f'model: str = "{best_model}"',
        content
    )
    config_file.write_text(new_content, encoding="utf-8")

    notify("VERONICA - Performance Mode",
           f"Performance mode active! Switched to {best_model}, Sir!")

    return (f"Performance Mode activated, Sir. "
            f"Switched to {best_model} model, "
            f"background apps closed, "
            f"high performance power plan enabled. "
            f"Please restart the agent for model change to take effect.")
    
# ── MODE MAP ──────────────────────────────────────────────────────
MODES = {
    "study":        activate_study_mode,
    "work":         activate_work_mode,
    "gaming":       activate_gaming_mode,
    "game":         activate_gaming_mode,
    "sleep":        activate_sleep_mode,
    "presentation": activate_presentation_mode,
    "present":      activate_presentation_mode,
    "night":        activate_night_mode,
    "performance":  activate_performance_mode,
    "fast":         activate_fast_mode,
    "speed":        activate_fast_mode,
    "boost":        activate_performance_mode,
}
def activate_mode(mode_name: str) -> str:
    fn = MODES.get(mode_name.lower().strip())
    if fn:
        return fn()
    available = ", ".join(MODES.keys())
    return f"Unknown mode: {mode_name}. Available modes: {available}, Sir."

if __name__ == "__main__":
    print("Testing modes...")
    print(activate_mode("study"))