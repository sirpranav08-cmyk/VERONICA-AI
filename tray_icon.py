"""
VERONICA System Tray Icon
"""
import pystray
from PIL import Image, ImageDraw
import subprocess
import threading

def create_icon():
    img = Image.new('RGB', (64, 64), '#020408')
    d = ImageDraw.Draw(img)
    d.ellipse([8,8,56,56], fill='#00f5ff', outline='#00f5ff')
    d.text((20,20), 'V', fill='#020408')
    return img

def open_veronica(icon, item):
    subprocess.Popen(
        [r"D:\jarvis-agent\desktop\node_modules\electron\dist\electron.exe", "."],
        cwd=r"D:\jarvis-agent\desktop"
    )

def quit_veronica(icon, item):
    icon.stop()

def run_tray():
    icon = pystray.Icon(
        "VERONICA",
        create_icon(),
        "VERONICA AI",
        menu=pystray.Menu(
            pystray.MenuItem("Open VERONICA", open_veronica, default=True),
            pystray.MenuItem("Quit", quit_veronica)
        )
    )
    print("[Tray] VERONICA tray icon started")
    icon.run()

if __name__ == "__main__":
    run_tray()
