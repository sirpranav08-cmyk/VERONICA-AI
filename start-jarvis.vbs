Set WshShell = CreateObject("WScript.Shell")

' Start Ollama silently
WshShell.Run "cmd /c set OLLAMA_HOST=0.0.0.0 && ollama serve", 0, False

' Wait for Ollama
WScript.Sleep 6000

' Start Agent silently
WshShell.Run "cmd /c cd /d D:\jarvis-agent\agent && call .venv\Scripts\activate && python main.py", 0, False

' Wait for Agent
WScript.Sleep 6000

' Start Mobile Server silently
WshShell.Run "cmd /c cd /d D:\jarvis-agent\mobile && npx expo start", 0, False

' Wait for Mobile Server
WScript.Sleep 5000

' Start Desktop App
WshShell.CurrentDirectory = "D:\jarvis-agent\desktop"
WshShell.Run "D:\jarvis-agent\desktop\node_modules\electron\dist\electron.exe D:\jarvis-agent\desktop", 1, False