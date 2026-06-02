import sys
import json
import asyncio
import uvicorn
import threading
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, '.')

from core.agent import JarvisAgent
from core.config import Config
import startup_briefing
import reminder_checker

# ── Background threads ──────────────────────────────────────────────
def run_briefing():
    import time
    time.sleep(5)
    startup_briefing.speak(startup_briefing.build_briefing())

threading.Thread(target=run_briefing, daemon=True).start()
threading.Thread(target=reminder_checker.check_reminders, daemon=True).start()

# ── FastAPI app ─────────────────────────────────────────────────────
app = FastAPI(title="JARVIS Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = JarvisAgent(Config())

# ── Routes ──────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "online", "model": Config().model}

@app.get("/tools")
async def list_tools():
    return {"tools": agent.get_tool_names()}

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
    print("[JARVIS] Client connected")
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            user_input = payload.get("message", "")
            async for chunk in agent.stream(user_input):
                await websocket.send_text(json.dumps(chunk))
    except WebSocketDisconnect:
        print("[JARVIS] Client disconnected")

if __name__ == "__main__":
    print("[JARVIS] Starting on http://127.0.0.1:8765")
    uvicorn.run(app, host="127.0.0.1", port=8765)