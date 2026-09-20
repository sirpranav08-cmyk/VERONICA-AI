# -*- coding: utf-8 -*-
import sys
import json
import asyncio
import uvicorn
import threading
import re
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware# Start AGI
try:
    from veronica_agi import start_agi
    agi = start_agi()
    print("[VERONICA] AGI core started — autonomous thinking active")
except Exception as e:
    print(f"[VERONICA] AGI skipped: {e}")
    agi = None
    

sys.path.insert(0, '.')

from core.agent import JarvisAgent
from core.config import Config
import startup_briefing
import reminder_checker
import jarvis_voice

# ── Background threads ──────────────────────────────────────────────
def run_briefing():
    import time
    time.sleep(5)
    startup_briefing.speak(startup_briefing.build_briefing())

threading.Thread(target=run_briefing, daemon=True).start()
threading.Thread(target=reminder_checker.check_reminders, daemon=True).start()

try:
    import autonomous
    autonomous.start_autonomous()
    print("[VERONICA] Autonomous engine started")
except Exception as e:
    print(f"[VERONICA] Autonomous engine skipped: {e}")

# ── FastAPI ─────────────────────────────────────────────────────────
app = FastAPI(title="VERONICA Agent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = JarvisAgent(Config())

def clean_for_speech(text: str) -> str:
    text = re.sub(r'http[s]?://\S+', '', text)
    text = re.sub(r'[A-Za-z]:\\[\w\\\.\-]+', '', text)
    text = re.sub(r'Executing \w+\.\.\.', '', text)
    text = re.sub(r'Tool error:.*', '', text)
    text = re.sub(r'[*#`⚙•]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:400]

# ── Routes ──────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "online", "model": Config().model}

@app.get("/tools")
async def list_tools():
    return {"tools": agent.get_tool_names()}

@app.get("/nn-stats")
async def nn_stats():
    import psutil
    ollama_mem = 0
    python_mem = 0
    for proc in psutil.process_iter(['name', 'memory_info']):
        try:
            if 'ollama' in proc.info['name'].lower():
                ollama_mem = proc.info['memory_info'].rss // 1024 // 1024
            if 'python' in proc.info['name'].lower():
                python_mem = proc.info['memory_info'].rss // 1024 // 1024
        except:
            pass
    return {
        "networks": [
            {"name": "LLaMA 3.2", "type": "Language Model", "status": "active",
             "memory_mb": ollama_mem, "parameters": "1B"},
            {"name": "Whisper", "type": "Speech Recognition", "status": "listening",
             "memory_mb": python_mem, "parameters": "39M"},
            {"name": "Edge TTS", "type": "Voice Synthesis", "status": "standby",
             "memory_mb": 0, "parameters": "Neural"},
            {"name": "ChromaDB", "type": "Memory Embeddings", "status": "active",
             "memory_mb": 50, "parameters": "Vectors"},
            {"name": "Wake Word", "type": "Wake Detection", "status": "listening",
             "memory_mb": 30, "parameters": "39M"},
        ],
        "total_cpu": psutil.cpu_percent(),
        "total_ram": psutil.virtual_memory().percent,
    }

@app.post("/listen")
async def listen_endpoint():
    try:
        import voice_input
        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, voice_input.listen_once, 5)
        print(f"[Voice] Transcribed: {text}")
        return {"text": text, "success": True}
    except Exception as e:
        print(f"[Voice] Error: {e}")
        return {"text": "", "success": False, "error": str(e)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[VERONICA] Client connected")
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            user_input = payload.get("message", "")
            client_type = payload.get("client_type", "desktop")
            full_response = ""

            try:
                async for chunk in agent.stream(user_input):
                    await websocket.send_text(json.dumps(chunk))
                    if chunk.get("type") == "token":
                        full_response += chunk.get("content", "")
            except Exception as e:
                print(f"[VERONICA] Stream error: {e}")
                err_msg = "I encountered an error, Sir. Please try again."
                await websocket.send_text(json.dumps({
                    "type": "token", "content": err_msg
                }))
                await websocket.send_text(json.dumps({"type": "done"}))
                full_response = err_msg

            # Speak ONCE after full response — desktop only
            if client_type == "desktop" and full_response.strip():
                clean = clean_for_speech(full_response)
                if clean and len(clean) > 3:
                    threading.Thread(
                        target=jarvis_voice.speak,
                        args=(clean,),
                        daemon=True
                    ).start()

    except WebSocketDisconnect:
        print("[VERONICA] Client disconnected")
    except Exception as e:
        print(f"[VERONICA] WebSocket error: {e}")

if __name__ == "__main__":
    print("[VERONICA] Starting on http://127.0.0.1:8765")
    uvicorn.run(app, host="0.0.0.0", port=8765)
