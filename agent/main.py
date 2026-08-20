"""
VERONICA Main Server
FastAPI + WebSocket agent server
"""
import json
import threading
import subprocess
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from core.agent import JarvisAgent
from core.config import Config
import jarvis_voice

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

config = Config()
agent = JarvisAgent(config)
connected_clients = set()

# ── STARTUP ───────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    print("[VERONICA] Starting up...")
    # Start emotion engine
    try:
        import emotions
        emotions.start()
        print("[VERONICA] Emotion engine active")
    except Exception as e:
        print(f"[VERONICA] Emotion error: {e}")
    # Start reminder checker
    import reminder_checker
    threading.Thread(target=reminder_checker.check_reminders, daemon=True).start()
    print("[Reminder] Checker started")

    # Start tray icon
    try:
        import tray_icon
        threading.Thread(target=tray_icon.run_tray, daemon=True).start()
        print("[VERONICA] Tray icon started")
    except Exception as e:
        print(f"[VERONICA] Tray icon error: {e}")

    # Start clipboard monitor
    try:
        import clipboard_monitor
        import win_notify
        def on_clip(text):
            if len(text) > 10:
                win_notify.notify("VERONICA", f"Copied: {text[:50]}...")
        clipboard_monitor.start(callback=on_clip)
        print("[VERONICA] Clipboard monitor started")
    except Exception as e:
        print(f"[VERONICA] Clipboard error: {e}")

    # Start hotkey listener
    try:
        import hotkey_listener
        threading.Thread(target=hotkey_listener.main, daemon=True).start()
        print("[VERONICA] Global hotkey Win+V active")
    except Exception as e:
        print(f"[VERONICA] Hotkey error: {e}")

    # Start always-on mic
    try:
        import always_on_mic
        always_on_mic.start()
        print("[VERONICA] Always-on mic started")
    except Exception as e:
        print(f"[VERONICA] Always-on mic error: {e}")

    # Start always-on face watch
    try:
        import face_watch
        face_watch.start(show_window=False)
        print("[VERONICA] Always-on face watch active")
    except Exception as e:
        print(f"[VERONICA] Face watch error: {e}")
        
    # Start autonomous decision engine
    try:
        import autonomous
        autonomous.start()
        print("[VERONICA] Autonomous decision engine active")
    except Exception as e:
        print(f"[VERONICA] Autonomous error: {e}")

    # Startup notification
    try:
        import win_notify
        threading.Thread(
            target=lambda: (__import__('time').sleep(3),
                          win_notify.notify("VERONICA", "All systems online, Sir.")),
            daemon=True
        ).start()
    except Exception as e:
        print(f"[VERONICA] Notify error: {e}")

    print("[VERONICA] All systems online!")
    
@app.get("/face_status")
async def face_status():
    try:
        import face_watch
        name = face_watch.last_seen or "No one"
        is_known = name not in ["No one", "Unknown", "Someone", None]
        # Calculate confidence from last detection time
        import time
        age = time.time() - face_watch.last_seen_time
        confidence = max(0, min(100, 100 - age * 5)) if is_known else 0
        return {
            "name": name,
            "confidence": confidence,
            "is_known": is_known,
            "last_seen": face_watch.last_seen_time
        }
    except Exception as e:
        return {"name": "No one", "confidence": 0, "is_known": False}

# ── HEALTH CHECK ─────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status": "online",
        "model": config.model,
        "agent": "VERONICA"
    }

# ── NN STATS ─────────────────────────────────────────────────────
@app.get("/nn-stats")
async def nn_stats():
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        return {
            "total_cpu": cpu,
            "total_ram": ram,
            "total_disk": disk
        }
    except:
        return {"total_cpu": 0, "total_ram": 0, "total_disk": 0}

# ── LISTEN ENDPOINT (Whisper STT) ────────────────────────────────
@app.post("/listen")
async def listen():
    try:
        from voice_input import record_and_transcribe
        text = record_and_transcribe(duration=5)
        if text and len(text.strip()) > 1:
            return {"success": True, "text": text.strip()}
        return {"success": False, "text": ""}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ── LISTEN RAW (Always-on mic) ────────────────────────────────────
@app.post("/listen_raw")
async def listen_raw(audio: UploadFile = File(...)):
    try:
        import tempfile, os
        from voice_input import transcribe_file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            content = await audio.read()
            f.write(content)
            tmp_path = f.name
        text = transcribe_file(tmp_path)
        os.unlink(tmp_path)
        if text and len(text.strip()) > 2:
            lower = text.lower().strip()
            wake_words = ['veronica', 'hey veronica', 'hi veronica', 'ok veronica']
            has_wake = any(w in lower for w in wake_words)
            if has_wake:
                cmd = lower
                for w in wake_words:
                    cmd = cmd.replace(w, '').strip()
                text = cmd if cmd else "hello"
                for client_ws in list(connected_clients):
                    try:
                        await client_ws.send_text(json.dumps({
                            "type": "voice_input",
                            "text": text
                        }))
                    except:
                        pass
                return {"success": True, "text": text}
        return {"success": False, "text": ""}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ── REMINDERS API ────────────────────────────────────────────────
@app.get("/reminders")
async def get_reminders_api():
    import json as _json
    from pathlib import Path
    f = Path("D:/jarvis-agent/agent/data/reminders.json")
    if not f.exists():
        return {"reminders": []}
    data = _json.loads(f.read_text())
    pending = [r for r in data if not r.get("done")]
    return {"reminders": pending}

@app.get("/predict")
async def predict():
    try:
        import self_dev
        return {
            "prediction": self_dev.predict_next_command(),
            "suggestion": self_dev.get_proactive_suggestion(),
            "stats": self_dev.get_stats()
        }
    except Exception as e:
        return {"error": str(e)}
    
# ── WEBSOCKET ─────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    print("[VERONICA] Client connected")
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            user_input = payload.get("message", "")
            client_type = payload.get("client_type", "desktop")
            full_response = ""

            try:
                # Log command for learning
                try:
                    import self_dev
                    self_dev.log_command(user_input, "", True, "")
                except: pass
                async for chunk in agent.stream(user_input):
                    if chunk.get("type") == "token":
                        chunk["content"] = (chunk.get("content", "")
                            .replace("Pranav RK", "you")
                            .replace("Pranav", "you"))
                        full_response += chunk.get("content", "")
                    await websocket.send_text(json.dumps(chunk))

                    if chunk.get("type") == "done":
                        if full_response.strip():
                            jarvis_voice.speak_async(full_response)
                        full_response = ""

            except Exception as e:
                print(f"[VERONICA] Stream error: {e}")
                await websocket.send_text(json.dumps({
                    "type": "token",
                    "content": f"Error, Sir: {str(e)[:100]}"
                }))
                await websocket.send_text(json.dumps({"type": "done"}))

    except WebSocketDisconnect:
        connected_clients.discard(websocket)
        print("[VERONICA] Client disconnected")

# ── FACE AUTH ON STARTUP ──────────────────────────────────────────
def startup_face_auth():
    try:
        import face_auth
        face_auth.load_model()
        if face_auth.labels:
            print("[VERONICA] Face authentication required...")
            success, name = face_auth.authenticate_face(timeout=15)
            if success:
                print(f"[VERONICA] Welcome back, {name}!")
                subprocess.Popen(
                    ["powershell", "-WindowStyle", "Hidden", "-Command",
                     f'Add-Type -AssemblyName System.Windows.Forms; $n=New-Object System.Windows.Forms.NotifyIcon; $n.Icon=[System.Drawing.SystemIcons]::Information; $n.Visible=$true; $n.BalloonTipTitle="VERONICA"; $n.BalloonTipText="Welcome back, {name}! Access granted."; $n.ShowBalloonTip(4000)'],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                print("[VERONICA] Face not recognized — shutting down!")
                import sys; sys.exit(1)
        else:
            print("[VERONICA] No faces registered — skipping auth")
    except Exception as e:
        print(f"[VERONICA] Face auth skipped: {e}")
        
@app.get("/emotion")
async def get_emotion():
    try:
        import emotions
        return emotions.get_current_emotion()
    except Exception as e:
        return {"emotion": "calm", "color": "#00f5ff"}

# ── MAIN ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Face authentication
    startup_face_auth()

    print("[VERONICA] Starting on http://0.0.0.0:8765")
    uvicorn.run(app, host="0.0.0.0", port=8765, log_level="info")