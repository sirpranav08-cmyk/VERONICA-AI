"""
One-time setup: download the Piper neural voice for VERONICA (en_US-amy, female, ~60MB).
Run from the agent/ folder:   python download_voice.py
"""
import os
import urllib.request

BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium"
VOICE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "data", "piper_voice")
FILES = {
    "en_US-amy-medium.onnx": f"{BASE}/en_US-amy-medium.onnx",
    "en_US-amy-medium.onnx.json": f"{BASE}/en_US-amy-medium.onnx.json",
}

def main():
    os.makedirs(VOICE_DIR, exist_ok=True)
    for name, url in FILES.items():
        dest = os.path.join(VOICE_DIR, name)
        if os.path.exists(dest):
            print(f"[Voice] Already have {name}")
            continue
        print(f"[Voice] Downloading {name} (~{ '60MB' if name.endswith('.onnx') else 'few KB' })...")
        urllib.request.urlretrieve(url, dest)
        print(f"[Voice] Saved -> {dest}")
    print("[Voice] Done! VERONICA's new voice is ready.")

if __name__ == "__main__":
    main()
