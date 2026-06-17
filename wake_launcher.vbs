Set WshShell = CreateObject("WScript.Shell")
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d D:\jarvis-agent\agent && .venv\Scripts\activate && python wake_word.py", 0, False
