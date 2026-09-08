"""
VERONICA Full Control Module
Complete PC, Internet, Communication control
"""
import subprocess
import os
import time
import pyautogui
import psutil
from pathlib import Path

# ── PC CONTROL ────────────────────────────────────────────────────

def get_all_processes():
    """List all running processes with details."""
    procs = []
    for p in psutil.process_iter(['name','pid','cpu_percent','memory_percent','status']):
        try:
            procs.append({
                'name': p.info['name'],
                'pid': p.info['pid'],
                'cpu': p.info['cpu_percent'],
                'mem': round(p.info['memory_percent'],1),
                'status': p.info['status']
            })
        except: pass
    return sorted(procs, key=lambda x: x['cpu'], reverse=True)[:20]

def control_window(action: str, title: str = "") -> str:
    """Control windows — minimize, maximize, close, focus."""
    try:
        import pygetwindow as gw
        if title:
            wins = gw.getWindowsWithTitle(title)
        else:
            wins = gw.getAllWindows()
        if not wins:
            return f"No window found: {title}"
        w = wins[0]
        if action == "minimize": w.minimize()
        elif action == "maximize": w.maximize()
        elif action == "close": w.close()
        elif action == "focus": w.activate()
        elif action == "restore": w.restore()
        return f"Window '{w.title}' {action}d, Sir."
    except Exception as e:
        return f"Window control error: {e}"

def type_anywhere(text: str, delay: float = 0.05) -> str:
    """Type text anywhere on screen."""
    pyautogui.write(text, interval=delay)
    return f"Typed: {text[:50]}, Sir."

def drag_and_drop(x1,y1,x2,y2) -> str:
    """Drag from one position to another."""
    pyautogui.moveTo(x1,y1,duration=0.3)
    pyautogui.dragTo(x2,y2,duration=0.5,button='left')
    return f"Dragged from ({x1},{y1}) to ({x2},{y2}), Sir."

def right_click(x,y) -> str:
    """Right click at position."""
    pyautogui.rightClick(x,y)
    return f"Right clicked at ({x},{y}), Sir."

def double_click(x,y) -> str:
    """Double click at position."""
    pyautogui.doubleClick(x,y)
    return f"Double clicked at ({x},{y}), Sir."

def get_screen_text() -> str:
    """Read all text from current screen using OCR."""
    try:
        import pytesseract
        img = pyautogui.screenshot()
        text = pytesseract.image_to_string(img)
        return text[:500] or "No text found, Sir."
    except Exception as e:
        return f"OCR error: {e}"

def move_file(src: str, dst: str) -> str:
    """Move a file from source to destination."""
    import shutil
    try:
        shutil.move(src, dst)
        return f"Moved {src} to {dst}, Sir."
    except Exception as e:
        return f"Move error: {e}"

def copy_file(src: str, dst: str) -> str:
    """Copy a file."""
    import shutil
    try:
        shutil.copy2(src, dst)
        return f"Copied {src} to {dst}, Sir."
    except Exception as e:
        return f"Copy error: {e}"

def search_files(query: str, path: str = "C:\\Users\\Admin") -> str:
    """Search for files by name."""
    results = []
    try:
        for root, dirs, files in os.walk(path):
            for f in files:
                if query.lower() in f.lower():
                    results.append(os.path.join(root, f))
            if len(results) >= 10:
                break
    except: pass
    return "\n".join(results) if results else f"No files found matching '{query}', Sir."

# ── INTERNET CONTROL ─────────────────────────────────────────────

def browse_web(url: str) -> str:
    """Open URL in browser."""
    if not url.startswith('http'):
        url = 'https://' + url
    subprocess.Popen(f'start chrome "{url}"', shell=True)
    return f"Opened {url}, Sir."

def download_file(url: str, save_path: str = "C:\\Users\\Admin\\Downloads") -> str:
    """Download a file from URL."""
    import requests
    try:
        filename = url.split('/')[-1] or 'download'
        filepath = os.path.join(save_path, filename)
        r = requests.get(url, stream=True, timeout=30)
        with open(filepath, 'wb') as f:
            for chunk in r.iter_content(1024*1024):
                f.write(chunk)
        return f"Downloaded to {filepath}, Sir."
    except Exception as e:
        return f"Download error: {e}"

def web_scrape(url: str) -> str:
    """Get text content from a webpage."""
    import requests
    from bs4 import BeautifulSoup
    try:
        r = requests.get(url, timeout=10,
            headers={'User-Agent':'Mozilla/5.0'})
        soup = BeautifulSoup(r.text, 'html.parser')
        text = ' '.join(soup.get_text().split())[:600]
        return text
    except Exception as e:
        return f"Scrape error: {e}"

def google_search_open(query: str) -> str:
    """Search Google and open results."""
    import urllib.parse
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    subprocess.Popen(f'start chrome "{url}"', shell=True)
    return f"Searching Google for: {query}, Sir."

def youtube_search(query: str) -> str:
    """Search YouTube."""
    import urllib.parse
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    subprocess.Popen(f'start chrome "{url}"', shell=True)
    return f"Searching YouTube for: {query}, Sir."

# ── WHATSAPP CONTROL ─────────────────────────────────────────────

def whatsapp_send(phone: str, message: str) -> str:
    """Send WhatsApp message via WhatsApp Web."""
    import urllib.parse
    clean_phone = phone.replace('+','').replace(' ','').replace('-','')
    msg_encoded = urllib.parse.quote(message)
    url = f"https://web.whatsapp.com/send?phone={clean_phone}&text={msg_encoded}"
    subprocess.Popen(f'start chrome "{url}"', shell=True)
    time.sleep(8)
    # Auto press Enter to send
    pyautogui.hotkey('ctrl', 'l')
    time.sleep(1)
    pyautogui.press('enter')
    return f"WhatsApp message sent to {phone}, Sir."

def whatsapp_open_chat(name: str) -> str:
    """Open WhatsApp Web and search for contact."""
    subprocess.Popen('start chrome "https://web.whatsapp.com"', shell=True)
    time.sleep(5)
    pyautogui.hotkey('ctrl', 'f')
    time.sleep(1)
    pyautogui.write(name, interval=0.05)
    return f"Opened WhatsApp chat for {name}, Sir."

# ── EMAIL CONTROL ────────────────────────────────────────────────

def send_email(to: str, subject: str, body: str,
               from_email: str = None, password: str = None) -> str:
    """Send email via Gmail SMTP."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    sender = from_email or os.getenv("EMAIL_ADDRESS", "")
    pwd = password or os.getenv("EMAIL_PASSWORD", "")

    if not sender or not pwd:
        return ("Email not configured, Sir. "
                "Please set EMAIL_ADDRESS and EMAIL_PASSWORD in .env file.")
    try:
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, pwd)
            server.send_message(msg)
        return f"Email sent to {to}, Sir."
    except Exception as e:
        return f"Email error: {e}"

def open_gmail() -> str:
    """Open Gmail in browser."""
    subprocess.Popen('start chrome "https://mail.google.com"', shell=True)
    return "Gmail opened, Sir."

# ── SYSTEM ADVANCED ──────────────────────────────────────────────

def get_installed_apps() -> str:
    """List all installed applications."""
    result = subprocess.run(
        ["powershell", "-Command",
         "Get-StartApps | Select-Object Name | Sort-Object Name"],
        capture_output=True, text=True
    )
    apps = result.stdout.strip()[:600]
    return apps or "Could not list apps, Sir."

def set_wallpaper(image_path: str) -> str:
    """Change desktop wallpaper."""
    subprocess.run([
        "powershell", "-Command",
        f"Add-Type -TypeDefinition 'using System.Runtime.InteropServices; public class W {{ [DllImport(\"user32.dll\")] public static extern int SystemParametersInfo(int a, int b, string c, int d); }}'; [W]::SystemParametersInfo(20, 0, '{image_path}', 3)"
    ], capture_output=True)
    return f"Wallpaper changed to {image_path}, Sir."

def get_weather(city: str = "Coimbatore") -> str:
    """Get weather for a city."""
    import requests
    try:
        url = f"https://wttr.in/{city}?format=3"
        r = requests.get(url, timeout=8)
        return r.text.strip() + ", Sir."
    except Exception as e:
        return f"Weather error: {e}"

def translate_text(text: str, target_lang: str = "ta") -> str:
    """Translate text using Google Translate."""
    import urllib.parse, urllib.request, json
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={urllib.parse.quote(text)}"
        r = urllib.request.urlopen(url, timeout=8)
        data = json.loads(r.read())
        return data[0][0][0]
    except Exception as e:
        return f"Translation error: {e}"