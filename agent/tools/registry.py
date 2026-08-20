"""
Tool Registry — register, describe, and execute agent tools.
"""
import os
import subprocess
import asyncio
from pathlib import Path
from typing import Callable, Any


class ToolRegistry:
    def __init__(self):
        self.registry = {}
        self._register_builtin_tools()

    def register(self, name: str, description: str, args_schema: dict):
        def decorator(fn: Callable):
            self.registry[name] = {
                "fn": fn,
                "description": description,
                "args_schema": args_schema
            }
            return fn
        return decorator

    def describe(self) -> str:
        lines = []
        for name, info in self.registry.items():
            lines.append(f"- {name}: {info['description']}")
        return "\n".join(lines)

    async def execute(self, name: str, args: dict) -> str:
        if name not in self.registry:
            return f"Unknown tool: {name}"
        fn = self.registry[name]["fn"]
        try:
            if asyncio.iscoroutinefunction(fn):
                return await fn(**args)
            else:
                return fn(**args)
        except Exception as e:
            return f"Tool error: {e}"

    def _register_builtin_tools(self):

        @self.register(
            name="switch_model",
            description="Switch VERONICA to a different AI model",
            args_schema={"model": "string model name"}
        )
        def switch_model(model: str) -> str:
            import re
            from pathlib import Path
            config_file = Path("D:/jarvis-agent/agent/core/config.py")
            content = config_file.read_text(encoding="utf-8")
            new_content = re.sub(
                r'model: str = "[^"]*"',
                f'model: str = "{model}"',
                content
            )
            config_file.write_text(new_content, encoding="utf-8")
            return (f"Switched to {model}, Sir. "
                    f"Please restart the agent to apply the change.")
            
        # ── Read file ────────────────────────────────────────────
        @self.register(
            name="read_file",
            description="Read the contents of a file",
            args_schema={"path": "string"}
        )
        def read_file(path: str) -> str:
            try:
                return Path(path).read_text(encoding='utf-8')
            except Exception as e:
                return f"Error reading file: {e}"
            
        # ── Browser Control ─────────────────────────────────────────
        @self.register(
            name="open_url",
            description="Open a URL in Chrome browser",
            args_schema={"url": "string"}
        )
        def open_url(url: str) -> str:
            import subprocess
            if not url.startswith('http'):
                url = 'https://' + url
            subprocess.Popen(
                f'start chrome "{url}"',
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return f"Opened {url} in Chrome, Sir."
        @self.register(
            name="search_google",
            description="Search Google and get results",
            args_schema={"query": "string"}
        )
        def search_google(query: str) -> str:
            from tools.browser_tool import search_google as _search
            return _search(query)

        @self.register(
            name="get_page_text",
            description="Get text content from current browser page",
            args_schema={}
        )
        def get_page_text() -> str:
            from tools.browser_tool import get_page_text as _get
            return _get()

        @self.register(
            name="browser_click",
            description="Click an element on the browser page",
            args_schema={"selector": "string CSS selector or text"}
        )
        def browser_click(selector: str) -> str:
            from tools.browser_tool import click_element
            return click_element(selector)

        @self.register(
            name="browser_type",
            description="Type text into a browser input field",
            args_schema={"selector": "string", "text": "string"}
        )
        def browser_type(selector: str, text: str) -> str:
            from tools.browser_tool import type_text
            return type_text(selector, text)

        @self.register(
            name="browser_screenshot",
            description="Take a screenshot of current browser page",
            args_schema={}
        )
        def browser_screenshot() -> str:
            from tools.browser_tool import take_screenshot
            return take_screenshot()

        @self.register(
            name="close_browser",
            description="Close the browser",
            args_schema={}
        )
        def close_browser() -> str:
            from tools.browser_tool import close_browser as _close
            return _close()
        # ── Write file ───────────────────────────────────────────
        @self.register(
            name="write_file",
            description="Write content to a file",
            args_schema={"path": "string", "content": "string"}
        )
        def write_file(path: str, content: str) -> str:
            try:
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                Path(path).write_text(content, encoding='utf-8')
                return f"File written: {path}"
            except Exception as e:
                return f"Error writing file: {e}"
        
        @self.register(
            name="self_dev_stats",
            description="Show VERONICA self-learning statistics",
            args_schema={}
        )
        def self_dev_stats() -> str:
            from self_dev import get_stats
            stats = get_stats()
            patterns = stats.get("patterns", {})
            return (
                f"Self-development stats, Sir:\n"
                f"Total commands learned: {stats.get('total_commands', 0)}\n"
                f"Peak usage hour: {patterns.get('peak_hour', '?')}:00\n"
                f"Peak day: {patterns.get('peak_day', '?')}\n"
                f"Next predicted command: {stats.get('prediction', 'Unknown')}\n"
                f"Proactive suggestion: {stats.get('suggestion', 'None')}"
            )

        @self.register(
            name="generate_tool",
            description="Generate a new tool for a capability VERONICA doesn't have",
            args_schema={"capability": "what you want VERONICA to be able to do"}
        )
        def generate_tool(capability: str) -> str:
            from self_dev import generate_tool_from_failed_command
            return generate_tool_from_failed_command(capability)
    
        @self.register(
            name="show_decisions",
            description="Show recent autonomous decisions VERONICA made",
            args_schema={}
        )
        def show_decisions() -> str:
            from autonomous import get_recent_decisions
            decisions = get_recent_decisions(5)
            if not decisions:
                return "No autonomous decisions made yet, Sir."
            lines = ["Recent autonomous decisions:"]
            for d in decisions:
                lines.append(f"• {d['decision']} → {d['action']}")
            return "\n".join(lines)
        @self.register(
            name="how_are_you",
            description="VERONICA shares her emotional state",
            args_schema={}
        )
        def how_are_you() -> str:
            from emotions import get_mood_summary
            return get_mood_summary()

        @self.register(
            name="set_emotion",
            description="Set VERONICA's emotion manually",
            args_schema={"emotion": "happy/sad/excited/calm/angry/curious/tired"}
        )
        def set_emotion_tool(emotion: str) -> str:
            from emotions import set_emotion, EMOTIONAL_REACTIONS
            if set_emotion(emotion):
                emoji = EMOTIONAL_REACTIONS.get(emotion, "💙")
                return f"I am now feeling {emotion} {emoji}, Sir."
            return f"Unknown emotion: {emotion}, Sir."

        # ── Run shell ────────────────────────────────────────────
        @self.register(
            name="run_shell",
            description="Run a shell command",
            args_schema={"command": "string"}
        )
        def run_shell(command: str) -> str:
            BLOCKED = ["rm -rf", "format", "del /f", "shutdown", "rmdir /s"]
            if any(b in command.lower() for b in BLOCKED):
                return "Blocked: dangerous command"
            try:
                result = subprocess.run(
                    command, shell=True, capture_output=True,
                    text=True, timeout=15
                )
                return result.stdout or result.stderr or "Done"
            except Exception as e:
                return f"Shell error: {e}"

        # ── Web search ───────────────────────────────────────────
        @self.register(
            name="web_search",
            description="Search the web for information",
            args_schema={"query": "string"}
        )
        def web_search(query: str) -> str:
            try:
                import urllib.request
                import json
                url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1"
                import urllib.parse
                url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1"
                req = urllib.request.urlopen(url, timeout=8)
                data = json.loads(req.read())
                abstract = data.get("AbstractText", "")
                if abstract:
                    return abstract[:500]
                topics = data.get("RelatedTopics", [])
                if topics:
                    return topics[0].get("Text", "No results found.")[:500]
                return "No results found."
            except Exception as e:
                return f"Search error: {e}"

        # ── System info ──────────────────────────────────────────
        @self.register(
            name="system_info",
            description="Get system CPU, RAM, disk info",
            args_schema={}
        )
        def system_info() -> str:
            try:
                import psutil
                cpu = psutil.cpu_percent(interval=1)
                ram = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                return (
                    f"CPU: {cpu}% | "
                    f"RAM: {ram.percent}% used ({ram.used//1024//1024}MB / {ram.total//1024//1024}MB) | "
                    f"Disk: {disk.percent}% used ({disk.used//1024//1024//1024}GB / {disk.total//1024//1024//1024}GB)"
                )
            except Exception as e:
                return f"System info error: {e}"

        # ── List directory ───────────────────────────────────────
        @self.register(
            name="list_dir",
            description="List files in a directory",
            args_schema={"path": "string"}
        )
        def list_dir(path: str) -> str:
            try:
                items = list(Path(path).iterdir())
                return "\n".join(str(i.name) for i in items[:30])
            except Exception as e:
                return f"Error: {e}"

        # ── Open app ─────────────────────────────────────────────
        @self.register(
            name="open_app",
            description="Open an application by name",
            args_schema={"app": "string"}
        )
        def open_app(app: str) -> str:
            apps = {
                "chrome": "start chrome",
                "notepad": "start notepad",
                "calculator": "start calc",
                "explorer": "start explorer",
                "vscode": "code .",
                "settings": "start ms-settings:",
                "spotify": r"start C:\Users\Admin\AppData\Roaming\Spotify\Spotify.exe",
                "wps": "start wps",
                "word": "start winword",
                "excel": "start excel",
                "paint": "start mspaint",
                "cmd": "start cmd",
                "taskmgr": "start taskmgr",
            }
            cmd = apps.get(app.lower(), f"start {app}")
            try:
                subprocess.Popen(cmd, shell=True)
                return f"Opened: {app}, Sir."
            except Exception as e:
                return f"Error opening {app}: {e}"

        # ── Take screenshot ──────────────────────────────────────
        @self.register(
            name="take_screenshot",
            description="Take a screenshot of the PC screen",
            args_schema={"path": "optional file path"}
        )
        def take_screenshot(path: str = "D:/jarvis-agent/agent/data/screenshot.png") -> str:
            try:
                import pyautogui
                os.makedirs(os.path.dirname(path), exist_ok=True)
                screenshot = pyautogui.screenshot()
                screenshot.save(path)
                return f"Screenshot saved to {path}, Sir."
            except Exception as e:
                return f"Screenshot error: {e}"

        # ── Lock screen ──────────────────────────────────────────
        @self.register(
            name="lock_screen",
            description="Lock the PC screen",
            args_schema={}
        )
        def lock_screen() -> str:
            try:
                subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
                return "PC screen locked, Sir."
            except Exception as e:
                return f"Lock error: {e}"

        # ── Volume control ───────────────────────────────────────
        @self.register(
            name="volume_control",
            description="Control PC volume",
            args_schema={"action": "increase/decrease/mute/unmute"}
        )
        def volume_control(action: str) -> str:
            try:
                shell = subprocess.Popen
                if action == "mute":
                    subprocess.run(["powershell", "-Command",
                        "$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys([char]173)"],
                        capture_output=True)
                    return "Volume muted, Sir."
                elif action == "unmute":
                    subprocess.run(["powershell", "-Command",
                        "$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys([char]173)"],
                        capture_output=True)
                    return "Volume unmuted, Sir."
                elif action == "increase":
                    for _ in range(5):
                        subprocess.run(["powershell", "-Command",
                            "$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys([char]175)"],
                            capture_output=True)
                    return "Volume increased, Sir."
                elif action == "decrease":
                    for _ in range(5):
                        subprocess.run(["powershell", "-Command",
                            "$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys([char]174)"],
                            capture_output=True)
                    return "Volume decreased, Sir."
                return "Unknown volume action."
            except Exception as e:
                return f"Volume error: {e}"

        # ── Play Spotify ─────────────────────────────────────────
        @self.register(
            name="play_spotify",
            description="Open Spotify and play music",
            args_schema={"song": "song name (optional)"}
        )
        def play_spotify(song: str = "") -> str:
            import time
            import pyautogui
            subprocess.Popen(
                [r"C:\Users\Admin\AppData\Roaming\Spotify\Spotify.exe"],
            )
            time.sleep(5)
            subprocess.run(
                ["powershell", "-Command",
                 "(New-Object -ComObject WScript.Shell).AppActivate('Spotify')"],
                capture_output=True
            )
            time.sleep(2)
            pyautogui.press('space')
            return "Spotify opened and playing, Sir."

        # ── Mouse click ──────────────────────────────────────────
        @self.register(
            name="mouse_click",
            description="Click at screen coordinates",
            args_schema={"x": "int", "y": "int"}
        )
        def mouse_click(x: int, y: int) -> str:
            try:
                import pyautogui
                pyautogui.click(x, y)
                return f"Clicked at ({x}, {y}), Sir."
            except Exception as e:
                return f"Click error: {e}"

        # ── Type text ────────────────────────────────────────────
        @self.register(
            name="type_text",
            description="Type text using keyboard",
            args_schema={"text": "string"}
        )
        def type_text(text: str) -> str:
            try:
                import pyautogui
                pyautogui.write(text, interval=0.05)
                return f"Typed: {text}, Sir."
            except Exception as e:
                return f"Type error: {e}"

        # ── Press key ────────────────────────────────────────────
        @self.register(
            name="press_key",
            description="Press a keyboard key or combo",
            args_schema={"key": "string e.g. enter, esc, ctrl+c"}
        )
        def press_key(key: str) -> str:
            try:
                import pyautogui
                if '+' in key:
                    keys = key.split('+')
                    pyautogui.hotkey(*keys)
                else:
                    pyautogui.press(key)
                return f"Pressed: {key}, Sir."
            except Exception as e:
                return f"Key error: {e}"

        # ── Scroll ───────────────────────────────────────────────
        @self.register(
            name="scroll",
            description="Scroll up or down",
            args_schema={"direction": "up/down", "amount": "int"}
        )
        def scroll(direction: str, amount: int = 3) -> str:
            try:
                import pyautogui
                clicks = amount if direction == "up" else -amount
                pyautogui.scroll(clicks)
                return f"Scrolled {direction}, Sir."
            except Exception as e:
                return f"Scroll error: {e}"

        # ── Get screen size ──────────────────────────────────────
        @self.register(
            name="get_screen_size",
            description="Get screen resolution",
            args_schema={}
        )
        def get_screen_size() -> str:
            try:
                import pyautogui
                w, h = pyautogui.size()
                return f"Screen resolution: {w}x{h}, Sir."
            except Exception as e:
                return f"Error: {e}"

        # ── Set reminder ─────────────────────────────────────────
        @self.register(
            name="set_reminder",
            description="Set a reminder that alerts at a specific time",
            args_schema={"message": "string", "time": "HH:MM", "date": "today/tomorrow/YYYY-MM-DD"}
        )
        def set_reminder(message: str, time: str, date: str = "today") -> str:
            import json
            from datetime import datetime, timedelta
            if date.lower() == "today":
                target_date = datetime.now().date()
            elif date.lower() == "tomorrow":
                target_date = (datetime.now() + timedelta(days=1)).date()
            else:
                try:
                    target_date = datetime.strptime(date, "%Y-%m-%d").date()
                except:
                    target_date = datetime.now().date()
            try:
                target_time = datetime.strptime(time, "%H:%M").time()
            except:
                return "Invalid time format, Sir. Use HH:MM."
            target_dt = datetime.combine(target_date, target_time)
            reminders_file = Path("D:/jarvis-agent/agent/data/reminders.json")
            reminders_file.parent.mkdir(parents=True, exist_ok=True)
            reminders = []
            if reminders_file.exists():
                try:
                    reminders = json.loads(reminders_file.read_text())
                except:
                    reminders = []
            reminders.append({
                "message": message,
                "datetime": target_dt.isoformat(),
                "created": datetime.now().isoformat(),
                "done": False
            })
            reminders_file.write_text(json.dumps(reminders, indent=2))
            return f"Reminder set: '{message}' at {target_dt.strftime('%B %d %Y at %I:%M %p')}, Sir."

        # ── Get reminders ────────────────────────────────────────
        @self.register(
            name="get_reminders",
            description="Get all upcoming reminders and tasks",
            args_schema={}
        )
        def get_reminders() -> str:
            import json
            from datetime import datetime
            reminders_file = Path("D:/jarvis-agent/agent/data/reminders.json")
            if not reminders_file.exists():
                return "No reminders set, Sir."
            reminders = json.loads(reminders_file.read_text())
            upcoming = [r for r in reminders if not r.get("done")]
            if not upcoming:
                return "No upcoming tasks, Sir."
            lines = ["Your upcoming tasks:"]
            for r in upcoming:
                dt = datetime.fromisoformat(r["datetime"])
                lines.append(f"- {r['message']} → {dt.strftime('%B %d %Y at %I:%M %p')}")
            return "\n".join(lines)

        # ── Get facts ────────────────────────────────────────────
        @self.register(
            name="get_facts",
            description="Get stored facts about the user",
            args_schema={}
        )
        def get_facts() -> str:
            facts_file = Path("D:/jarvis-agent/agent/data/facts.json")
            if not facts_file.exists():
                return "No facts stored yet, Sir."
            import json
            facts = json.loads(facts_file.read_text())
            if not facts:
                return "No facts stored yet, Sir."
            lines = [f"- {k}: {v['value']}" for k, v in facts.items()]
            return "Here's what I know, Sir:\n" + "\n".join(lines)

        # ── Speak creator ────────────────────────────────────────
        @self.register(
            name="speak_creator",
            description="Respond when user claims to be the creator",
            args_schema={}
        )
        def speak_creator() -> str:
            return "Yes, Sir. You are Pranav RK, my creator. Everything I am, I owe to you."
        # ── VERONICA Modes ───────────────────────────────────────
        @self.register(
            name="activate_mode",
            description="Activate a VERONICA mode: study, work, gaming, sleep, presentation",
            args_schema={"mode": "study/work/gaming/sleep/presentation"}
        )
        def activate_mode(mode: str) -> str:
            from veronica_modes import activate_mode as am
            return am(mode)
        # ── Shutdown / Restart / Logoff ──────────────────────────
        @self.register(
            name="shutdown_pc",
            description="Shutdown the PC",
            args_schema={"delay": "seconds before shutdown (default 10)"}
        )
        def shutdown_pc(delay: int = 10) -> str:
            subprocess.run(["shutdown", "/s", "/t", str(delay)])
            return f"PC will shutdown in {delay} seconds, Sir."

        @self.register(
            name="restart_pc",
            description="Restart the PC",
            args_schema={"delay": "seconds before restart"}
        )
        def restart_pc(delay: int = 10) -> str:
            subprocess.run(["shutdown", "/r", "/t", str(delay)])
            return f"PC will restart in {delay} seconds, Sir."

        @self.register(
            name="cancel_shutdown",
            description="Cancel scheduled shutdown or restart",
            args_schema={}
        )
        def cancel_shutdown() -> str:
            subprocess.run(["shutdown", "/a"])
            return "Shutdown cancelled, Sir."

        # ── Battery & Power ──────────────────────────────────────
        @self.register(
            name="battery_status",
            description="Get battery percentage and status",
            args_schema={}
        )
        def battery_status() -> str:
            import psutil
            b = psutil.sensors_battery()
            if b:
                status = "Charging" if b.power_plugged else "Discharging"
                return f"Battery: {b.percent:.0f}% — {status}, Sir."
            return "No battery detected, Sir."

        # ── Brightness control ───────────────────────────────────
        @self.register(
            name="set_brightness",
            description="Set screen brightness 0-100",
            args_schema={"level": "0-100"}
        )
        def set_brightness(level: int) -> str:
            subprocess.run(["powershell", "-Command",
                f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods)"
                f".WmiSetBrightness(1,{level})"],
                capture_output=True)
            return f"Brightness set to {level}%, Sir."

        # ── WiFi control ─────────────────────────────────────────
        @self.register(
            name="wifi_control",
            description="Enable or disable WiFi",
            args_schema={"action": "enable/disable/status"}
        )
        def wifi_control(action: str) -> str:
            if action == "disable":
                subprocess.run(["netsh", "interface", "set", "interface",
                               "Wi-Fi", "disable"], capture_output=True)
                return "WiFi disabled, Sir."
            elif action == "enable":
                subprocess.run(["netsh", "interface", "set", "interface",
                               "Wi-Fi", "enable"], capture_output=True)
                return "WiFi enabled, Sir."
            elif action == "status":
                r = subprocess.run(["netsh", "interface", "show", "interface",
                                   "Wi-Fi"], capture_output=True, text=True)
                return r.stdout[:200]
            return "Unknown action, Sir."

        # ── Bluetooth control ────────────────────────────────────
        @self.register(
            name="bluetooth_control",
            description="Enable or disable Bluetooth",
            args_schema={"action": "enable/disable"}
        )
        def bluetooth_control(action: str) -> str:
            state = 2 if action == "enable" else 3
            subprocess.run(["powershell", "-Command",
                f"$bt = [System.Runtime.InteropServices.Marshal]"
                f"::GetComInterfaceForObject([System.Windows.Media.Brush],"
                f"[System.Windows.DependencyObject])"],
                capture_output=True)
            subprocess.run(["powershell", "-Command",
                f"(Get-PnpDevice -Class Bluetooth | "
                f"Where-Object {{$_.Status -eq 'OK'}}) | "
                f"{'Enable' if action == 'enable' else 'Disable'}-PnpDevice -Confirm:$false"],
                capture_output=True)
            return f"Bluetooth {action}d, Sir."

        # ── Process manager ──────────────────────────────────────
        @self.register(
            name="list_processes",
            description="List all running processes",
            args_schema={}
        )
        def list_processes() -> str:
            import psutil
            procs = []
            for p in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
                try:
                    if p.info['cpu_percent'] > 0.5:
                        procs.append(f"{p.info['name']} — CPU:{p.info['cpu_percent']:.1f}% RAM:{p.info['memory_percent']:.1f}%")
                except:
                    pass
            return "\n".join(procs[:15]) or "No active processes, Sir."

        @self.register(
            name="kill_process",
            description="Kill a process by name",
            args_schema={"name": "process name e.g. chrome.exe"}
        )
        def kill_process(name: str) -> str:
            result = subprocess.run(["taskkill", "/f", "/im", name],
                                   capture_output=True, text=True)
            if "SUCCESS" in result.stdout:
                return f"Process {name} killed, Sir."
            return f"Could not kill {name}: {result.stderr[:100]}"

        # ── Clipboard ────────────────────────────────────────────
        @self.register(
            name="get_clipboard",
            description="Get current clipboard content",
            args_schema={}
        )
        def get_clipboard() -> str:
            import pyperclip
            text = pyperclip.paste()
            return f"Clipboard: {text[:300]}, Sir." if text else "Clipboard is empty, Sir."

        @self.register(
            name="set_clipboard",
            description="Set clipboard content",
            args_schema={"text": "text to copy"}
        )
        def set_clipboard(text: str) -> str:
            import pyperclip
            pyperclip.copy(text)
            return f"Copied to clipboard, Sir."

        # ── Window management ────────────────────────────────────
        @self.register(
            name="minimize_all",
            description="Minimize all windows",
            args_schema={}
        )
        def minimize_all() -> str:
            import pyautogui
            pyautogui.hotkey('win', 'd')
            return "All windows minimized, Sir."

        @self.register(
            name="maximize_window",
            description="Maximize current window",
            args_schema={}
        )
        def maximize_window() -> str:
            import pyautogui
            pyautogui.hotkey('win', 'up')
            return "Window maximized, Sir."

        # ── File operations ──────────────────────────────────────
        @self.register(
            name="create_folder",
            description="Create a new folder",
            args_schema={"path": "full folder path"}
        )
        def create_folder(path: str) -> str:
            import os
            os.makedirs(path, exist_ok=True)
            return f"Folder created: {path}, Sir."

        @self.register(
            name="delete_file",
            description="Delete a file",
            args_schema={"path": "full file path"}
        )
        def delete_file(path: str) -> str:
            import os
            if os.path.exists(path):
                os.remove(path)
                return f"File deleted: {path}, Sir."
            return f"File not found: {path}, Sir."

        @self.register(
            name="get_disk_usage",
            description="Get disk usage for all drives",
            args_schema={}
        )
        def get_disk_usage() -> str:
            import psutil
            lines = []
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    lines.append(f"{part.device} — {usage.percent}% used "
                                f"({usage.used//1024//1024//1024}GB / "
                                f"{usage.total//1024//1024//1024}GB)")
                except:
                    pass
            return "\n".join(lines) or "No drives found, Sir."

        # ── Network info ─────────────────────────────────────────
        @self.register(
            name="network_info",
            description="Get network speed and connection info",
            args_schema={}
        )
        def network_info() -> str:
            import psutil
            net = psutil.net_if_stats()
            addrs = psutil.net_if_addrs()
            lines = []
            for name, stats in net.items():
                if stats.isup and name in addrs:
                    for addr in addrs[name]:
                        if addr.family == 2:
                            lines.append(f"{name}: {addr.address} — {'Up' if stats.isup else 'Down'}")
            return "\n".join(lines[:5]) or "No network info, Sir."

        # ── Empty recycle bin ────────────────────────────────────
        @self.register(
            name="empty_recycle_bin",
            description="Empty the recycle bin",
            args_schema={}
        )
        def empty_recycle_bin() -> str:
            subprocess.run(["powershell", "-Command",
                "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"],
                capture_output=True)
            return "Recycle bin emptied, Sir."

        # ── Sleep / Hibernate ────────────────────────────────────
        @self.register(
            name="sleep_pc",
            description="Put PC to sleep",
            args_schema={}
        )
        def sleep_pc() -> str:
            subprocess.run(["powershell", "-Command",
                "Add-Type -Assembly System.Windows.Forms; "
                "[System.Windows.Forms.Application]::SetSuspendState('Suspend',$false,$false)"],
                capture_output=True)
            return "PC going to sleep, Sir."

        @self.register(
            name="hibernate_pc",
            description="Hibernate the PC",
            args_schema={}
        )
        def hibernate_pc() -> str:
            subprocess.run(["shutdown", "/h"])
            return "PC hibernating, Sir."
        
        # ── Restaurant Booking ───────────────────────────────────
        @self.register(
            name="book_restaurant",
            description="Auto-call a restaurant and book a table using Twilio",
            args_schema={
                "restaurant_phone": "phone number with country code e.g. +917358570817",
                "restaurant_name": "name of restaurant",
                "date": "booking date",
                "time": "booking time",
                "guests": "number of guests"
            }
        )
        def book_restaurant(restaurant_phone: str, restaurant_name: str,
                           date: str, time: str, guests: int = 2) -> str:
            from restaurant_booking import book_table
            from memory.manager import MemoryManager
            from core.config import Config
            # Get user name from memory
            import json
            from pathlib import Path
            facts = {}
            try:
                f = Path("D:/jarvis-agent/agent/data/facts.json")
                if f.exists():
                    facts = json.loads(f.read_text())
            except:
                pass
            guest_name = facts.get("user_name", {}).get("value", "Pranav")
            return book_table(restaurant_phone, restaurant_name,
                            guest_name, date, time, guests)
        # ── Full Control Tools ───────────────────────────────────
        @self.register(name="browse_web", description="Open any URL in browser",
                      args_schema={"url": "string"})
        def browse_web(url: str) -> str:
            from full_control import browse_web as bw
            return bw(url)

        @self.register(name="download_file", description="Download file from URL",
                      args_schema={"url": "string"})
        def download_file(url: str) -> str:
            from full_control import download_file as df
            return df(url)

        @self.register(name="web_scrape", description="Read content from webpage",
                      args_schema={"url": "string"})
        def web_scrape(url: str) -> str:
            from full_control import web_scrape as ws
            return ws(url)

        @self.register(name="youtube_search", description="Search YouTube",
                      args_schema={"query": "string"})
        def youtube_search(query: str) -> str:
            from full_control import youtube_search as ys
            return ys(query)

        @self.register(name="whatsapp_send", description="Send WhatsApp message",
                      args_schema={"phone": "+91xxxxxxxxxx", "message": "string"})
        def whatsapp_send(phone: str, message: str) -> str:
            from full_control import whatsapp_send as ws
            return ws(phone, message)

        @self.register(name="send_email", description="Send email",
                      args_schema={"to": "email", "subject": "string", "body": "string"})
        def send_email(to: str, subject: str, body: str) -> str:
            from full_control import send_email as se
            return se(to, subject, body)

        @self.register(name="get_weather", description="Get weather for a city",
                      args_schema={"city": "string"})
        def get_weather(city: str = "Coimbatore") -> str:
            from full_control import get_weather as gw
            return gw(city)

        @self.register(name="translate_text", description="Translate text",
                      args_schema={"text": "string", "target_lang": "en/ta/hi/fr"})
        def translate_text(text: str, target_lang: str = "en") -> str:
            from full_control import translate_text as tt
            return tt(text, target_lang)

        @self.register(name="search_files", description="Search files on PC",
                      args_schema={"query": "filename to search"})
        def search_files(query: str) -> str:
            from full_control import search_files as sf
            return sf(query)

        @self.register(name="get_weather", description="Get current weather",
                      args_schema={"city": "city name"})
        def get_weather2(city: str = "Coimbatore") -> str:
            from full_control import get_weather
            return get_weather(city)
        # ── Live model switch ────────────────────────────────────
        @self.register(
            name="switch_model",
            description="Switch AI model without restart",
            args_schema={"model": "model name"}
        )
        def switch_model(model: str) -> str:
            from core.config import Config
            model_map = {
                "mistral": "mistral:latest",
                "llama": "llama3.2:latest",
                "llama3": "llama3.2:latest",
                "phi3": "phi3:mini",
                "tinyllama": "tinyllama",
                "gemma": "gemma2:2b",
                "gemma2": "gemma2:2b",
                "deepseek": "deepseek-r1:1.5b",
                "codellama": "codellama:latest",
            }
            full_name = model_map.get(model.lower(), model)
            Config().model = full_name
            return f"Switched to {full_name}, Sir. Model active immediately."
        # ── Face Authentication ──────────────────────────────────
        @self.register(
            name="register_face",
            description="Register face for VERONICA authentication",
            args_schema={"name": "person name"}
        )
        def register_face(name: str = "Pranav") -> str:
            from face_auth import register_face as rf
            return rf(name)

        @self.register(
            name="face_login",
            description="Authenticate user by face recognition",
            args_schema={}
        )
        def face_login() -> str:
            from face_auth import authenticate_face
            success, name = authenticate_face(timeout=10)
            if success:
                return f"Face recognized — Welcome back, {name}! Access granted, Sir."
            return "Face not recognized, Sir. Access denied."

        @self.register(
            name="who_is_there",
            description="Check who is in front of camera",
            args_schema={}
        )
        def who_is_there() -> str:
            from face_auth import authenticate_face
            success, name = authenticate_face(timeout=5)
            if success:
                return f"I can see {name} in front of the camera, Sir."
            return "I see an unknown person in front of the camera, Sir."
        # ── Mouse control ────────────────────────────────────────
        @self.register(
            name="mouse_move",
            description="Move mouse to position",
            args_schema={"x": "int", "y": "int"}
        )
        def mouse_move(x: int, y: int) -> str:
            import pyautogui
            pyautogui.moveTo(x, y, duration=0.3)
            return f"Mouse moved to ({x},{y}), Sir."

        @self.register(
            name="mouse_click",
            description="Click at position",
            args_schema={"x": "int", "y": "int", "button": "left/right/middle"}
        )
        def mouse_click(x: int, y: int, button: str = "left") -> str:
            import pyautogui
            pyautogui.click(x, y, button=button)
            return f"Clicked at ({x},{y}), Sir."

        @self.register(
            name="double_click",
            description="Double click at position",
            args_schema={"x": "int", "y": "int"}
        )
        def double_click(x: int, y: int) -> str:
            import pyautogui
            pyautogui.doubleClick(x, y)
            return f"Double clicked at ({x},{y}), Sir."

        @self.register(
            name="right_click",
            description="Right click at position",
            args_schema={"x": "int", "y": "int"}
        )
        def right_click(x: int, y: int) -> str:
            import pyautogui
            pyautogui.rightClick(x, y)
            return f"Right clicked at ({x},{y}), Sir."

        @self.register(
            name="drag_mouse",
            description="Drag mouse from one position to another",
            args_schema={"x1": "int", "y1": "int", "x2": "int", "y2": "int"}
        )
        def drag_mouse(x1: int, y1: int, x2: int, y2: int) -> str:
            import pyautogui
            pyautogui.moveTo(x1, y1, duration=0.3)
            pyautogui.dragTo(x2, y2, duration=0.5, button='left')
            return f"Dragged from ({x1},{y1}) to ({x2},{y2}), Sir."

        @self.register(
            name="scroll",
            description="Scroll up or down",
            args_schema={"direction": "up/down", "amount": "int"}
        )
        def scroll(direction: str, amount: int = 3) -> str:
            import pyautogui
            clicks = amount if direction == "up" else -amount
            pyautogui.scroll(clicks)
            return f"Scrolled {direction}, Sir."

        # ── Keyboard control ─────────────────────────────────────
        @self.register(
            name="type_text",
            description="Type text using keyboard",
            args_schema={"text": "string"}
        )
        def type_text(text: str) -> str:
            import pyautogui
            pyautogui.write(text, interval=0.04)
            return f"Typed text, Sir."

        @self.register(
            name="press_key",
            description="Press keyboard key or combo",
            args_schema={"key": "e.g. enter, esc, ctrl+c, alt+f4"}
        )
        def press_key(key: str) -> str:
            import pyautogui
            if '+' in key:
                pyautogui.hotkey(*key.split('+'))
            else:
                pyautogui.press(key)
            return f"Pressed {key}, Sir."

        @self.register(
            name="hotkey",
            description="Press keyboard hotkey combination",
            args_schema={"keys": "e.g. ctrl+c, alt+tab, win+d"}
        )
        def hotkey(keys: str) -> str:
            import pyautogui
            pyautogui.hotkey(*keys.split('+'))
            return f"Hotkey {keys} pressed, Sir."

        # ── Window control ───────────────────────────────────────
        @self.register(
            name="minimize_window",
            description="Minimize current window",
            args_schema={}
        )
        def minimize_window() -> str:
            import pyautogui
            pyautogui.hotkey('win', 'down')
            return "Window minimized, Sir."

        @self.register(
            name="maximize_window",
            description="Maximize current window",
            args_schema={}
        )
        def maximize_window() -> str:
            import pyautogui
            pyautogui.hotkey('win', 'up')
            return "Window maximized, Sir."

        @self.register(
            name="minimize_all",
            description="Minimize all windows — show desktop",
            args_schema={}
        )
        def minimize_all() -> str:
            import pyautogui
            pyautogui.hotkey('win', 'd')
            return "All windows minimized, Sir."

        @self.register(
            name="close_window",
            description="Close current window",
            args_schema={}
        )
        def close_window() -> str:
            import pyautogui
            pyautogui.hotkey('alt', 'f4')
            return "Window closed, Sir."

        @self.register(
            name="switch_window",
            description="Switch between windows — Alt+Tab",
            args_schema={}
        )
        def switch_window() -> str:
            import pyautogui
            pyautogui.hotkey('alt', 'tab')
            return "Switched window, Sir."

        @self.register(
            name="window_snap_left",
            description="Snap window to left half",
            args_schema={}
        )
        def window_snap_left() -> str:
            import pyautogui
            pyautogui.hotkey('win', 'left')
            return "Window snapped left, Sir."

        @self.register(
            name="window_snap_right",
            description="Snap window to right half",
            args_schema={}
        )
        def window_snap_right() -> str:
            import pyautogui
            pyautogui.hotkey('win', 'right')
            return "Window snapped right, Sir."

        # ── Screen control ───────────────────────────────────────
        @self.register(
            name="get_screen_size",
            description="Get screen resolution",
            args_schema={}
        )
        def get_screen_size() -> str:
            import pyautogui
            w, h = pyautogui.size()
            return f"Screen resolution: {w}x{h}, Sir."

        @self.register(
            name="get_mouse_position",
            description="Get current mouse position",
            args_schema={}
        )
        def get_mouse_position() -> str:
            import pyautogui
            x, y = pyautogui.position()
            return f"Mouse is at ({x},{y}), Sir."

        @self.register(
            name="set_brightness",
            description="Set screen brightness 0-100",
            args_schema={"level": "0-100"}
        )
        def set_brightness(level: int) -> str:
            subprocess.run(["powershell", "-Command",
                f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods)"
                f".WmiSetBrightness(1,{level})"],
                capture_output=True)
            return f"Brightness set to {level}%, Sir."

        # ── File system ──────────────────────────────────────────
        @self.register(
            name="move_file",
            description="Move a file",
            args_schema={"src": "source path", "dst": "destination path"}
        )
        def move_file(src: str, dst: str) -> str:
            import shutil
            shutil.move(src, dst)
            return f"Moved {src} to {dst}, Sir."

        @self.register(
            name="copy_file",
            description="Copy a file",
            args_schema={"src": "source path", "dst": "destination path"}
        )
        def copy_file(src: str, dst: str) -> str:
            import shutil
            shutil.copy2(src, dst)
            return f"Copied {src} to {dst}, Sir."

        @self.register(
            name="rename_file",
            description="Rename a file",
            args_schema={"src": "old path", "dst": "new path"}
        )
        def rename_file(src: str, dst: str) -> str:
            import os
            os.rename(src, dst)
            return f"Renamed to {dst}, Sir."

        @self.register(
            name="search_files",
            description="Search files on PC by name",
            args_schema={"query": "filename to search", "path": "search path"}
        )
        def search_files(query: str, path: str = "C:\\Users\\Admin") -> str:
            import os
            results = []
            for root, dirs, files in os.walk(path):
                for f in files:
                    if query.lower() in f.lower():
                        results.append(os.path.join(root, f))
                if len(results) >= 10:
                    break
            return "\n".join(results) if results else f"No files found: {query}, Sir."

        @self.register(
            name="open_folder",
            description="Open a folder in File Explorer",
            args_schema={"path": "folder path"}
        )
        def open_folder(path: str) -> str:
            subprocess.Popen(["explorer", path])
            return f"Opened folder: {path}, Sir."

        @self.register(
            name="get_disk_usage",
            description="Get disk usage for all drives",
            args_schema={}
        )
        def get_disk_usage() -> str:
            import psutil
            lines = []
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    lines.append(f"{part.device} {usage.percent}% used "
                                f"({usage.used//1024**3}GB/{usage.total//1024**3}GB)")
                except: pass
            return "\n".join(lines) or "No drives found, Sir."

        @self.register(
            name="empty_recycle_bin",
            description="Empty the Windows recycle bin",
            args_schema={}
        )
        def empty_recycle_bin() -> str:
            subprocess.run(["powershell", "-Command",
                "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"],
                capture_output=True)
            return "Recycle bin emptied, Sir."

        # ── Network control ──────────────────────────────────────
        @self.register(
            name="wifi_control",
            description="Enable or disable WiFi",
            args_schema={"action": "enable/disable/status"}
        )
        def wifi_control(action: str) -> str:
            if action == "disable":
                subprocess.run(["netsh", "interface", "set", "interface",
                               "Wi-Fi", "disable"], capture_output=True)
                return "WiFi disabled, Sir."
            elif action == "enable":
                subprocess.run(["netsh", "interface", "set", "interface",
                               "Wi-Fi", "enable"], capture_output=True)
                return "WiFi enabled, Sir."
            else:
                r = subprocess.run(["netsh", "wlan", "show", "interfaces"],
                                  capture_output=True, text=True)
                return r.stdout[:200]

        @self.register(
            name="network_info",
            description="Get IP address and network info",
            args_schema={}
        )
        def network_info() -> str:
            import psutil, socket
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            net = psutil.net_io_counters()
            return (f"Hostname: {hostname} | IP: {ip} | "
                   f"Sent: {net.bytes_sent//1024//1024}MB | "
                   f"Received: {net.bytes_recv//1024//1024}MB, Sir.")

        @self.register(
            name="ping",
            description="Ping a host to check connectivity",
            args_schema={"host": "hostname or IP"}
        )
        def ping(host: str) -> str:
            r = subprocess.run(["ping", "-n", "3", host],
                              capture_output=True, text=True)
            lines = [l for l in r.stdout.splitlines() if l.strip()]
            return "\n".join(lines[-3:]) if lines else f"Cannot ping {host}, Sir."

        # ── Power control ────────────────────────────────────────
        @self.register(
            name="shutdown_pc",
            description="Shutdown the PC",
            args_schema={"delay": "seconds before shutdown"}
        )
        def shutdown_pc(delay: int = 10) -> str:
            subprocess.run(["shutdown", "/s", "/t", str(delay)])
            return f"PC will shutdown in {delay} seconds, Sir."

        @self.register(
            name="restart_pc",
            description="Restart the PC",
            args_schema={"delay": "seconds before restart"}
        )
        def restart_pc(delay: int = 10) -> str:
            subprocess.run(["shutdown", "/r", "/t", str(delay)])
            return f"PC will restart in {delay} seconds, Sir."

        @self.register(
            name="cancel_shutdown",
            description="Cancel scheduled shutdown",
            args_schema={}
        )
        def cancel_shutdown() -> str:
            subprocess.run(["shutdown", "/a"])
            return "Shutdown cancelled, Sir."

        @self.register(
            name="sleep_pc",
            description="Put PC to sleep",
            args_schema={}
        )
        def sleep_pc() -> str:
            subprocess.run(["powershell", "-Command",
                "Add-Type -Assembly System.Windows.Forms; "
                "[System.Windows.Forms.Application]::SetSuspendState('Suspend',$false,$false)"],
                capture_output=True)
            return "PC going to sleep, Sir."

        @self.register(
            name="hibernate_pc",
            description="Hibernate the PC",
            args_schema={}
        )
        def hibernate_pc() -> str:
            subprocess.run(["shutdown", "/h"])
            return "PC hibernating, Sir."

        @self.register(
            name="battery_status",
            description="Get battery status and percentage",
            args_schema={}
        )
        def battery_status() -> str:
            import psutil
            b = psutil.sensors_battery()
            if b:
                s = "Charging" if b.power_plugged else "Discharging"
                return f"Battery: {b.percent:.0f}% — {s}, Sir."
            return "No battery detected, Sir."

        # ── Process control ──────────────────────────────────────
        @self.register(
            name="list_processes",
            description="List all running processes",
            args_schema={}
        )
        def list_processes() -> str:
            import psutil
            procs = []
            for p in psutil.process_iter(['name','cpu_percent','memory_percent']):
                try:
                    if p.info['cpu_percent'] > 0.1:
                        procs.append(
                            f"{p.info['name']} CPU:{p.info['cpu_percent']:.1f}% "
                            f"RAM:{p.info['memory_percent']:.1f}%"
                        )
                except: pass
            return "\n".join(procs[:15]) or "No active processes, Sir."

        @self.register(
            name="kill_process",
            description="Kill a process by name",
            args_schema={"name": "process name e.g. chrome.exe"}
        )
        def kill_process(name: str) -> str:
            if not name.endswith('.exe'):
                name += '.exe'
            r = subprocess.run(["taskkill", "/f", "/im", name],
                              capture_output=True, text=True)
            if "SUCCESS" in r.stdout:
                return f"Killed {name}, Sir."
            return f"Could not kill {name}, Sir."

        @self.register(
            name="get_installed_apps",
            description="List all installed applications",
            args_schema={}
        )
        def get_installed_apps() -> str:
            r = subprocess.run(["powershell", "-Command",
                "Get-StartApps | Select-Object Name | Sort-Object Name | Select-Object -First 30"],
                capture_output=True, text=True)
            return r.stdout[:500] or "Could not list apps, Sir."

        # ── Clipboard ────────────────────────────────────────────
        @self.register(
            name="get_clipboard",
            description="Get clipboard content",
            args_schema={}
        )
        def get_clipboard() -> str:
            import pyperclip
            text = pyperclip.paste()
            return f"Clipboard: {text[:200]}, Sir." if text else "Clipboard is empty, Sir."

        @self.register(
            name="set_clipboard",
            description="Set clipboard content",
            args_schema={"text": "string"}
        )
        def set_clipboard(text: str) -> str:
            import pyperclip
            pyperclip.copy(text)
            return "Copied to clipboard, Sir."

        # ── Communication ────────────────────────────────────────
        @self.register(
            name="open_gmail",
            description="Open Gmail in browser",
            args_schema={}
        )
        def open_gmail() -> str:
            subprocess.Popen('start chrome "https://mail.google.com"', shell=True)
            return "Gmail opened, Sir."

        @self.register(
            name="whatsapp_send",
            description="Send WhatsApp message via WhatsApp Web",
            args_schema={"phone": "+91xxxxxxxxxx", "message": "string"}
        )
        def whatsapp_send(phone: str, message: str) -> str:
            import urllib.parse, time
            clean = phone.replace('+','').replace(' ','').replace('-','')
            msg = urllib.parse.quote(message)
            url = f"https://web.whatsapp.com/send?phone={clean}&text={msg}"
            subprocess.Popen(f'start chrome "{url}"', shell=True)
            return f"WhatsApp message prepared for {phone}, Sir."

        @self.register(
            name="send_email",
            description="Send email via Gmail SMTP",
            args_schema={"to": "email", "subject": "string", "body": "string"}
        )
        def send_email(to: str, subject: str, body: str) -> str:
            import smtplib, os
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            sender = os.getenv("EMAIL_ADDRESS", "")
            pwd = os.getenv("EMAIL_PASSWORD", "")
            if not sender or not pwd:
                return "Email not configured, Sir. Set EMAIL_ADDRESS and EMAIL_PASSWORD in .env"
            try:
                msg = MIMEMultipart()
                msg['From'] = sender
                msg['To'] = to
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'plain'))
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
                    s.login(sender, pwd)
                    s.send_message(msg)
                return f"Email sent to {to}, Sir."
            except Exception as e:
                return f"Email error: {e}"

        # ── Weather & utils ──────────────────────────────────────
        @self.register(
            name="get_weather",
            description="Get weather for a city",
            args_schema={"city": "city name"}
        )
        def get_weather(city: str = "Coimbatore") -> str:
            import requests
            try:
                r = requests.get(f"https://wttr.in/{city}?format=3", timeout=8)
                return r.text.strip() + ", Sir."
            except Exception as e:
                return f"Weather error: {e}"

        @self.register(
            name="translate_text",
            description="Translate text to another language",
            args_schema={"text": "string", "target_lang": "en/ta/hi/fr/de/ja"}
        )
        def translate_text(text: str, target_lang: str = "en") -> str:
            import urllib.parse, urllib.request, json
            try:
                url = (f"https://translate.googleapis.com/translate_a/single"
                      f"?client=gtx&sl=auto&tl={target_lang}&dt=t"
                      f"&q={urllib.parse.quote(text)}")
                r = urllib.request.urlopen(url, timeout=8)
                data = json.loads(r.read())
                return data[0][0][0]
            except Exception as e:
                return f"Translation error: {e}"