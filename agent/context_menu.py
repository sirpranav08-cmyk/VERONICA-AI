"""
VERONICA Right-click Context Menu
Adds VERONICA option to Windows Explorer
"""
import subprocess
import winreg

def add_context_menu():
    """Add VERONICA to right-click menu for files and folders."""
    try:
        # For files
        key_path = r"*\shell\VERONICA"
        key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path)
        winreg.SetValue(key, "", winreg.REG_SZ, "Ask VERONICA")
        winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ,
            r"D:\jarvis-agent\desktop\node_modules\electron\dist\electron.exe,0")

        cmd_key = winreg.CreateKey(key, "command")
        winreg.SetValue(cmd_key, "", winreg.REG_SZ,
            r'D:\jarvis-agent\desktop\node_modules\electron\dist\electron.exe . "%1"')

        # For folders
        folder_key_path = r"Directory\shell\VERONICA"
        folder_key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, folder_key_path)
        winreg.SetValue(folder_key, "", winreg.REG_SZ, "Ask VERONICA about this folder")
        winreg.SetValueEx(folder_key, "Icon", 0, winreg.REG_SZ,
            r"D:\jarvis-agent\desktop\node_modules\electron\dist\electron.exe,0")

        folder_cmd = winreg.CreateKey(folder_key, "command")
        winreg.SetValue(folder_cmd, "", winreg.REG_SZ,
            r'D:\jarvis-agent\desktop\node_modules\electron\dist\electron.exe . "%1"')

        print("[Context Menu] VERONICA added to right-click menu!")
        return "VERONICA added to right-click menu, Sir."
    except Exception as e:
        return f"Context menu error: {e}"

def remove_context_menu():
    """Remove VERONICA from right-click menu."""
    try:
        winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, r"*\shell\VERONICA\command")
        winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, r"*\shell\VERONICA")
        winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, r"Directory\shell\VERONICA\command")
        winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, r"Directory\shell\VERONICA")
        return "VERONICA removed from right-click menu, Sir."
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    print(add_context_menu())
