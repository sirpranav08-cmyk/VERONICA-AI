@echo off
if not DEFINED IS_MINIMIZED set IS_MINIMIZED=1 && start "" /min "%~dpnx0" %* && exit
title JARVIS AI - Auto Start
echo [JARVIS] Waiting for system to fully load...
timeout /t 15 /nobreak
echo [JARVIS] Starting Agent...
cd /d D:\jarvis-agent\agent
call .venv\Scripts\activate
start /min "" python main.py
timeout /t 5 /nobreak
echo [JARVIS] Launching Desktop App...
cd /d D:\jarvis-agent\desktop
start "" node_modules\electron\dist\electron.exe .
start /min "" cmd /c "cd /d D:\jarvis-agent\agent && .venv\Scripts\activate && python wake_word.py"
exit