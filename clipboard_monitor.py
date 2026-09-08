"""
VERONICA Clipboard Monitor
Watches clipboard and can process copied text
"""
import pyperclip
import time
import threading

last_clip = ""
on_change_callback = None

def monitor():
    global last_clip
    print("[Clipboard] Monitor started")
    while True:
        try:
            current = pyperclip.paste()
            if current != last_clip and current.strip():
                last_clip = current
                print(f"[Clipboard] New content: {current[:50]}...")
                if on_change_callback:
                    on_change_callback(current)
        except:
            pass
        time.sleep(1)

def start(callback=None):
    global on_change_callback
    on_change_callback = callback
    t = threading.Thread(target=monitor, daemon=True)
    t.start()

if __name__ == "__main__":
    start()
    input("Monitoring clipboard... Press Enter to stop\n")
