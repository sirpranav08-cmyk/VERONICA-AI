"""
VERONICA Screen OCR
Reads text from any part of the screen
"""
import pyautogui
import pytesseract
from PIL import Image
import subprocess
import os

# Set tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def read_screen(x=None, y=None, w=None, h=None) -> str:
    """Read text from screen. If no coords given, reads full screen."""
    try:
        if x is not None:
            img = pyautogui.screenshot(region=(x, y, w, h))
        else:
            img = pyautogui.screenshot()
        text = pytesseract.image_to_string(img).strip()
        return text if text else "No text found on screen, Sir."
    except Exception as e:
        return f"OCR error: {e}"

def install_tesseract():
    print("[OCR] Tesseract not found. Installing...")
    subprocess.run([
        "winget", "install", "UB-Mannheim.TesseractOCR"
    ])

if __name__ == "__main__":
    print(read_screen())
