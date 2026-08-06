@echo off
title JARVIS AI
echo [JARVIS] Waiting for Ollama...
timeout /t 8 /nobreak

echo [JARVIS] Starting Agent...
cd /d D:\jarvis-agent\agent
call .venv\Scripts\activate
start /min "" cmd /c "cd /d D:\jarvis-agent\agent && .venv\Scripts\activate && python main.py"

timeout /t 5 /nobreak

echo [JARVIS] Launching Desktop App...
start /min "" cmd /c "cd /d D:\jarvis-agent\desktop && node_modules\electron\dist\electron.exe ."

timeout /t 3 /nobreak

echo [JARVIS] Starting Mobile Server...
start /min "" cmd /c "cd /d D:\jarvis-agent\mobile && npx expo start"

echo [JARVIS] All systems online.
exit