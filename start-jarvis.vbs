Set WshShell = CreateObject("WScript.Shell")

' Start agent silently
WshShell.Run "cmd /c cd /d D:\jarvis-agent\agent && .venv\Scripts\activate && python main.py", 0, False

' Wait for agent to load
WScript.Sleep 8000

' Start wake word listener silently
WshShell.Run "cmd /c cd /d D:\jarvis-agent\agent && .venv\Scripts\activate && python wake_word.py", 0, False

' Wait
WScript.Sleep 2000

' Start desktop app from correct directory
WshShell.CurrentDirectory = "D:\jarvis-agent\desktop"
WshShell.Run "D:\jarvis-agent\desktop\node_modules\electron\dist\electron.exe D:\jarvis-agent\desktop", 1, False