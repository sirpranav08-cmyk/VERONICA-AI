"""
VERONICA Main Server — Complete Integration
FastAPI + WebSocket + All Features
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
    print("[VERONICA] Starting all systems...")

    # Reminder checker
    try:
        import reminder_checker
        threading.Thread(target=reminder_checker.check_reminders,
                        daemon=True).start()
        print("[Reminder] Checker started")
    except Exception as e:
        print(f"[Reminder] Error: {e}")

    # System tray
    try:
        import tray_icon
        threading.Thread(target=tray_icon.run_tray, daemon=True).start()
        print("[Tray] Icon started")
    except Exception as e:
        print(f"[Tray] Error: {e}")

    # Clipboard monitor
    try:
        import clipboard_monitor
        import win_notify
        def on_clip(text):
            if len(text) > 10:
                win_notify.notify("VERONICA", f"Copied: {text[:50]}...")
        clipboard_monitor.start(callback=on_clip)
        print("[Clipboard] Monitor started")
    except Exception as e:
        print(f"[Clipboard] Error: {e}")

    # Global hotkey
    try:
        import hotkey_listener
        threading.Thread(target=hotkey_listener.main, daemon=True).start()
        print("[Hotkey] Win+V active")
    except Exception as e:
        print(f"[Hotkey] Error: {e}")

    # Always-on mic
    try:
        import always_on_mic
        always_on_mic.start()
        print("[Mic] Always-on mic started")
    except Exception as e:
        print(f"[Mic] Error: {e}")

    # Face watch
    try:
        import face_watch
        face_watch.start(show_window=False)
        print("[Face] Always-on face watch active")
    except Exception as e:
        print(f"[Face] Error: {e}")

    # Emotion engine
    try:
        import emotions
        emotions.start()
        print("[Emotions] Engine active")
    except Exception as e:
        print(f"[Emotions] Error: {e}")
        
    # Start rational agent
    try:
        import rational_agent
        rational_agent.start(agent.tools)
        print("[VERONICA] Rational agent active")
    except Exception as e:
        print(f"[Rational] Error: {e}")  

    # Autonomous decisions
    try:
        import autonomous
        autonomous.start()
        print("[Autonomous] Decision engine active")
    except Exception as e:
        print(f"[Autonomous] Error: {e}")

    # Self development
    try:
        import self_dev
        self_dev.start()
        print("[SelfDev] Self-development engine active")
    except Exception as e:
        print(f"[SelfDev] Error: {e}")

    # Siri features
    try:
        import siri_features
        siri_features.start()
        print("[Siri] Siri-style features active")
    except Exception as e:
        print(f"[Siri] Error: {e}")

    # Startup notification
    try:
        import win_notify
        threading.Thread(
            target=lambda: (
                __import__('time').sleep(3),
                win_notify.notify("VERONICA", "All systems online, Sir.")
            ), daemon=True
        ).start()
    except Exception as e:
        print(f"[Notify] Error: {e}")

    print("[VERONICA] ✓ All systems online!")

# ── HEALTH ────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "online", "model": config.model, "agent": "VERONICA"}

# ── STATS ─────────────────────────────────────────────────────────
@app.get("/nn-stats")
async def nn_stats():
    try:
        import psutil
        return {
            "total_cpu": psutil.cpu_percent(interval=0.1),
            "total_ram": psutil.virtual_memory().percent,
            "total_disk": psutil.disk_usage('/').percent
        }
    except:
        return {"total_cpu": 0, "total_ram": 0, "total_disk": 0}

# ── EMOTION ───────────────────────────────────────────────────────
@app.get("/emotion")
async def get_emotion():
    try:
        import emotions
        return emotions.get_current_emotion()
    except:
        return {"emotion": "calm", "color": "#00f5ff",
                "emoji": "💙", "mood_score": 50, "energy": 0.7}

# ── FACE STATUS ───────────────────────────────────────────────────
@app.get("/face_status")
async def face_status():
    try:
        import face_watch, time
        name = face_watch.last_seen or "No one"
        is_known = name not in ["No one", "Unknown", "Someone", None]
        age = time.time() - face_watch.last_seen_time
        confidence = max(0, min(100, 100 - age * 5)) if is_known else 0
        return {"name": name, "confidence": confidence, "is_known": is_known}
    except:
        return {"name": "No one", "confidence": 0, "is_known": False}

# ── REMINDERS ─────────────────────────────────────────────────────
@app.get("/reminders")
async def get_reminders_api():
    from pathlib import Path
    f = Path("D:/jarvis-agent/agent/data/reminders.json")
    if not f.exists():
        return {"reminders": []}
    data = json.loads(f.read_text())
    return {"reminders": [r for r in data if not r.get("done")]}

# ── PREDICT ───────────────────────────────────────────────────────
@app.get("/predict")
async def predict():
    try:
        import self_dev
        return {
            "prediction": self_dev.predict_next_command(),
            "suggestion": self_dev.get_proactive_suggestion()
        }
    except Exception as e:
        return {"error": str(e)}

# ── DECISIONS ─────────────────────────────────────────────────────
@app.get("/decisions")
async def get_decisions():
    try:
        import autonomous
        return {"decisions": autonomous.get_recent_decisions(10)}
    except:
        return {"decisions": []}

# ── LISTEN ────────────────────────────────────────────────────────
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

# ── LISTEN RAW ────────────────────────────────────────────────────
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
            wake_words = ['veronica', 'hey veronica', 'hi veronica',
                         'ok veronica']
            if any(w in lower for w in wake_words):
                cmd = lower
                for w in wake_words:
                    cmd = cmd.replace(w, '').strip()
                text = cmd if cmd else "hello"
                for client_ws in list(connected_clients):
                    try:
                        await client_ws.send_text(json.dumps({
                            "type": "voice_input", "text": text
                        }))
                    except: pass
                return {"success": True, "text": text}
        return {"success": False, "text": ""}
    except Exception as e:
        return {"success": False, "error": str(e)}

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
            user_emotion = "neutral"

            # Log command
            try:
                import self_dev
                self_dev.log_command(user_input, "", True, "")
            except: pass

            # Update emotion
            try:
                import emotions
                user_emotion = emotions.detect_user_emotion(user_input)
                emotions.update_emotion("interaction", user_emotion)
            except: pass

            # Check small talk FIRST
            try:
                import siri_features
                small_talk = siri_features.check_small_talk(user_input)
                if small_talk:
                    await websocket.send_text(json.dumps(
                        {"type": "token", "content": small_talk}))
                    await websocket.send_text(json.dumps(
                        {"type": "done"}))
                    jarvis_voice.speak_async(small_talk)
                    continue
            except: pass

            # Check shortcuts
            try:
                import siri_features
                user_input = siri_features.resolve_context(user_input)
                shortcut = siri_features.get_shortcut(user_input)
                if shortcut:
                    action = shortcut.get("action")
                    args = {k: v for k, v in shortcut.items()
                           if k != "action"}
                    result = await agent.tools.execute(action, args)
                    await websocket.send_text(json.dumps(
                        {"type": "token", "content": result}))
                    await websocket.send_text(json.dumps(
                        {"type": "done"}))
                    jarvis_voice.speak_async(result)
                    continue
            except: pass

            # Stream response
            try:
                async for chunk in agent.stream(user_input):
                    if chunk.get("type") == "token":
                        chunk["content"] = (chunk.get("content", "")
                            .replace("Pranav RK", "you")
                            .replace("Pranav", "you"))
                        full_response += chunk.get("content", "")
                    await websocket.send_text(json.dumps(chunk))

                    if chunk.get("type") == "done":
                        if full_response.strip():
                            try:
                                import emotions
                                emotional = emotions.add_emotion_to_response(
                                    full_response, "task", user_emotion)
                                jarvis_voice.speak_async(emotional)
                                emotion_state = emotions.get_current_emotion()
                                await websocket.send_text(json.dumps({
                                    "type": "emotion",
                                    "state": emotion_state
                                }))
                            except:
                                jarvis_voice.speak_async(full_response)

                            try:
                                import siri_features
                                siri_features.update_context(
                                    user_input, "", full_response)
                            except: pass

                            try:
                                import self_dev
                                self_dev.log_command(
                                    user_input, "", True,
                                    full_response[:100])
                            except: pass

                        full_response = ""

            except Exception as e:
                print(f"[VERONICA] Stream error: {e}")
                error_msg = f"I encountered an error, Sir: {str(e)[:100]}"
                await websocket.send_text(json.dumps(
                    {"type": "token", "content": error_msg}))
                await websocket.send_text(json.dumps({"type": "done"}))
                try:
                    import self_dev
                    self_dev.log_error(str(e), user_input)
                except: pass

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
                     f'Add-Type -AssemblyName System.Windows.Forms; '
                     f'$n=New-Object System.Windows.Forms.NotifyIcon; '
                     f'$n.Icon=[System.Drawing.SystemIcons]::Information; '
                     f'$n.Visible=$true; '
                     f'$n.BalloonTipTitle="VERONICA"; '
                     f'$n.BalloonTipText="Welcome back, {name}! Access granted."; '
                     f'$n.ShowBalloonTip(4000)'],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                print("[VERONICA] Face not recognized — shutting down!")
                import sys; sys.exit(1)
        else:
            print("[VERONICA] No faces registered — skipping auth")
    except Exception as e:
        print(f"[VERONICA] Face auth skipped: {e}")

# ── MAIN ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    startup_face_auth()
    print("[VERONICA] Starting server on http://0.0.0.0:8765")
    uvicorn.run(app, host="0.0.0.0", port=8765, log_level="info")