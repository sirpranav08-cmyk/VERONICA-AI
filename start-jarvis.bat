@echo off
title JARVIS AI
echo [JARVIS] Waiting for Ollama...
timeout /t 8 /nobreak
echo [JARVIS] Starting Agent...
cd /d D:\jarvis-agent\agent
call .venv\Scripts\activate
start "" python main.py
timeout /t 3 /nobreak
echo [JARVIS] Launching Desktop App...
cd /d D:\jarvis-agent\desktop
call node_modules\.bin\electron .