"""
JARVIS Voice Engine — Microsoft Zira (Female) + Edge TTS
"""
import os
import subprocess
import asyncio
import tempfile
import edge_tts

VOICE = "en-US-JennyNeural"  # Edge TTS voice
RATE = "+5%"
PITCH = "+0Hz"

async def _generate_speech(text: str, output_path: str):
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    await communicate.save(output_path)

def speak(text: str):
    if not text or len(text.strip()) < 2:
        return

    safe = text.replace("'", "").replace('"', '').replace('\n', ' ')[:400]

    # Method 1 — Edge TTS mp3 via mciSendString
    try:
        tmp = os.path.join(tempfile.gettempdir(), "jarvis_tts.mp3")
        asyncio.run(_generate_speech(safe, tmp))
        tmp_win = tmp.replace('\\', '\\\\')
        script = f"""
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public class MCI {{
    [DllImport("winmm.dll", CharSet=CharSet.Auto)]
    public static extern int mciSendString(string cmd, System.Text.StringBuilder ret, int retLen, IntPtr hwnd);
}}
'@
[MCI]::mciSendString('open "{tmp}" type mpegvideo alias snd', $null, 0, [IntPtr]::Zero)
[MCI]::mciSendString('play snd wait', $null, 0, [IntPtr]::Zero)
[MCI]::mciSendString('close snd', $null, 0, [IntPtr]::Zero)
""".replace("{tmp}", tmp)
        result = subprocess.run(
            ["powershell", "-WindowStyle", "Hidden", "-Command", script],
            capture_output=True, timeout=60
        )
        if result.returncode == 0:
            print(f"[Voice] Edge TTS spoke: {safe[:50]}...")
            return
    except Exception as e:
        print(f"[Voice] Edge TTS failed: {e}")

    # Method 2 — Microsoft Zira (guaranteed to work)
    try:
        script = f"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice('Microsoft Zira Desktop')
$s.Rate = 1
$s.Volume = 100
$s.Speak('{safe}')
"""
        subprocess.run(
            ["powershell", "-WindowStyle", "Hidden", "-Command", script],
            timeout=60
        )
        print(f"[Voice] Zira spoke: {safe[:50]}...")
    except Exception as e:
        print(f"[Voice] Zira failed: {e}")

def speak_async(text: str):
    import threading
    threading.Thread(target=speak, args=(text,), daemon=True).start()

if __name__ == "__main__":
    print("Testing JARVIS Zira voice...")
    speak("Hello Pranav. I am VERONICA your personal assistant. All systems are online.")