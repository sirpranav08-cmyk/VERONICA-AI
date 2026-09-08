"""
VERONICA Windows Toast Notifications
"""
import subprocess

def notify(title: str, message: str, duration: int = 5):
    script = f'''
Add-Type -AssemblyName System.Windows.Forms
$notify = New-Object System.Windows.Forms.NotifyIcon
$notify.Icon = [System.Drawing.SystemIcons]::Information
$notify.Visible = $true
$notify.BalloonTipIcon = "Info"
$notify.BalloonTipTitle = "{title}"
$notify.BalloonTipText = "{message}"
$notify.ShowBalloonTip({duration * 1000})
Start-Sleep -Seconds {duration + 1}
$notify.Dispose()
'''
    subprocess.Popen(
        ["powershell", "-WindowStyle", "Hidden", "-Command", script],
        creationflags=subprocess.CREATE_NO_WINDOW
    )

if __name__ == "__main__":
    notify("VERONICA", "All systems online, Sir.")
