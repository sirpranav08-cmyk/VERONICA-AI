Set WshShell = CreateObject("WScript.Shell")

' Kill any existing processes
WshShell.Run "taskkill /F /IM python.exe", 0, True
WshShell.Run "taskkill /F /IM electron.exe", 0, True

' Wait
WScript.Sleep 3000

' Start Ollama
WshShell.Run "ollama serve", 0, False

' Wait for Ollama
WScript.Sleep 5000

' Start agent
WshShell.Run "cmd /c cd /d D:\jarvis-agent\agent && .venv\Scripts\activate && python main.py", 0, False

' Wait for agent to fully load
WScript.Sleep 10000

' Start desktop app
WshShell.CurrentDirectory = "D:\jarvis-agent\desktop"
WshShell.Run "D:\jarvis-agent\desktop\node_modules\electron\dist\electron.exe D:\jarvis-agent\desktop", 1, False