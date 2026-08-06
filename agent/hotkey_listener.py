
"""
Global hotkey listener - Win+V opens VERONICA anywhere on Windows
"""
import keyboard
import subprocess
import time
import os

DESKTOP_APP = r"D:\jarvis-agent\desktop\node_modules\electron\dist\electron.exe"
DESKTOP_DIR = r"D:\jarvis-agent\desktop"

def is_veronica_open():
    result = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq electron.exe"],
        capture_output=True, text=True
    )
    return "electron.exe" in result.stdout

def open_veronica():
    if is_veronica_open():
        # Bring to front
        subprocess.run([
            "powershell", "-Command",
            "(New-Object -ComObject WScript.Shell).AppActivate('VERONICA')"
        ], capture_output=True)
        print("[Hotkey] VERONICA brought to front")
    else:
        # Open app
        subprocess.Popen(
            [DESKTOP_APP, "."],
            cwd=DESKTOP_DIR,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        print("[Hotkey] VERONICA opened")

def main():
    print("[Hotkey] Listener started - Press Win+V to open VERONICA")
    keyboard.add_hotkey('windows+v', open_veronica)
    keyboard.wait()

if __name__ == "__main__":
    main()
