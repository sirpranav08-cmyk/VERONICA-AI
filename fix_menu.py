import winreg

# Pass file path as argument to electron
cmd_file = r'D:\jarvis-agent\desktop\node_modules\electron\dist\electron.exe D:\jarvis-agent\desktop --file="%1"'
cmd_folder = r'D:\jarvis-agent\desktop\node_modules\electron\dist\electron.exe D:\jarvis-agent\desktop --folder="%1"'

# Fix files
k = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r'*\shell\VERONICA\command', 0, winreg.KEY_SET_VALUE)
winreg.SetValue(k, '', winreg.REG_SZ, cmd_file)
winreg.CloseKey(k)

# Fix folders
k2 = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r'Directory\shell\VERONICA\command', 0, winreg.KEY_SET_VALUE)
winreg.SetValue(k2, '', winreg.REG_SZ, cmd_folder)
winreg.CloseKey(k2)

print('Fixed!')