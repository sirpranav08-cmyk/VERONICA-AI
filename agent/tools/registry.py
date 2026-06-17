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
        self.registry: dict[str, dict] = {}
        self._register_builtin_tools()

    def register(self, name: str, description: str, args_schema: dict):
        def decorator(fn: Callable):
            self.registry[name] = {
                "fn": fn,
                "description": description,
                "args": args_schema,
            }
            return fn
        return decorator

    async def execute(self, name: str, args: dict) -> str:
        if name not in self.registry:
            return f"Unknown tool: {name}"
        fn = self.registry[name]["fn"]
        if asyncio.iscoroutinefunction(fn):
            return await fn(**args)
        return fn(**args)

    def describe(self) -> str:
        lines = []
        for name, meta in self.registry.items():
            lines.append(f"- {name}: {meta['description']} | args: {meta['args']}")
        return "\n".join(lines)

    def _register_builtin_tools(self):

        @self.register(
            name="read_file",
            description="Read contents of a file",
            args_schema={"path": "string"}
        )
        def read_file(path: str) -> str:
            try:
                return Path(path).read_text(encoding="utf-8")
            except Exception as e:
                return f"Error: {e}"

        @self.register(
            name="write_file",
            description="Write content to a file (creates if not exists)",
            args_schema={"path": "string", "content": "string"}
        )
        def write_file(path: str, content: str) -> str:
            try:
                p = Path(path)
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
                return f"Written {len(content)} chars to {path}"
            except Exception as e:
                return f"Error: {e}"

        @self.register(
            name="list_directory",
            description="List files and folders in a directory",
            args_schema={"path": "string"}
        )
        def list_directory(path: str = ".") -> str:
            try:
                entries = list(Path(path).iterdir())
                return "\n".join(str(e) for e in sorted(entries))
            except Exception as e:
                return f"Error: {e}"

        @self.register(
            name="run_shell",
            description="Run a shell command and return stdout",
            args_schema={"command": "string"}
        )
        def run_shell(command: str) -> str:
            BLOCKED = ["rm -rf", "sudo", "mkfs", "dd if=", ":(){"]
            for b in BLOCKED:
                if b in command:
                    return f"Blocked: '{b}' is not permitted."
            try:
                result = subprocess.run(
                    command, shell=True, capture_output=True,
                    text=True, timeout=15
                )
                out = result.stdout or result.stderr
                return out[:3000] if out else "(no output)"
            except subprocess.TimeoutExpired:
                return "Command timed out (15s limit)"
            except Exception as e:
                return f"Error: {e}"

        @self.register(
            name="web_search",
            description="Search the web for current information",
            args_schema={"query": "string"}
        )
        async def web_search(query: str) -> str:
            try:
                import httpx
                url = "https://api.duckduckgo.com/"
                params = {"q": query, "format": "json", "no_html": "1"}
                async with httpx.AsyncClient(timeout=10) as client:
                    r = await client.get(url, params=params)
                    data = r.json()
                abstract = data.get("AbstractText", "")
                related = [t["Text"] for t in data.get("RelatedTopics", [])[:3] if "Text" in t]
                if abstract:
                    return abstract
                elif related:
                    return "\n".join(related)
                else:
                    return f"No results found for: {query}"
            except Exception as e:
                return f"Search error: {e}"

        @self.register(
            name="system_info",
            description="Get system info: OS, CPU, memory, disk",
            args_schema={}
        )
        def system_info() -> str:
            try:
                import platform, psutil
                mem = psutil.virtual_memory()
                disk = psutil.disk_usage("/")
                return (
                    f"OS: {platform.system()} {platform.release()}\n"
                    f"CPU: {psutil.cpu_percent()}% ({psutil.cpu_count()} cores)\n"
                    f"RAM: {mem.used // 1024**2}MB / {mem.total // 1024**2}MB\n"
                    f"Disk: {disk.used // 1024**3}GB / {disk.total // 1024**3}GB"
                )
            except Exception as e:
                return f"Error: {e}"

        @self.register(
            name="recall_memory",
            description="Search long-term memory for past context",
            args_schema={"query": "string"}
        )
        def recall_memory(query: str) -> str:
            return "Memory recall: connect MemoryManager instance for full recall."

        @self.register(
            name="set_reminder",
            description="Set a reminder that fires a popup at a specific time",
            args_schema={"message": "string", "time": "string HH:MM 24hr", "date": "string today/tomorrow/YYYY-MM-DD"}
        )
        def set_reminder(message: str, time: str, date: str = "today") -> str:
            import json
            from datetime import datetime, timedelta

            now = datetime.now()
            
            # Handle day names
            day_map = {
                "monday": 0, "tuesday": 1, "wednesday": 2,
                "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
            }
            
            if date.lower() in day_map:
                target_day = day_map[date.lower()]
                current_day = now.weekday()
                days_ahead = target_day - current_day
                if days_ahead <= 0:
                    days_ahead += 7
                target_date = (now + timedelta(days=days_ahead)).date()
            elif date.lower() == "today":
                target_date = now.date()
            elif date.lower() == "tomorrow":
                target_date = (now + timedelta(days=1)).date()
            else:
                try:
                    target_date = datetime.strptime(date, "%Y-%m-%d").date()
                except:
                    target_date = now.date()

            try:
                target_time = datetime.strptime(time, "%H:%M").time()
            except:
                return "Invalid time. Use HH:MM format like 17:00"

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
                "created": now.isoformat(),
                "done": False
            })
            reminders_file.write_text(json.dumps(reminders, indent=2))
            return f"Reminder set: '{message}' at {target_dt.strftime('%B %d %Y at %I:%M %p')}"

        @self.register(
            name="get_reminders",
            description="Get all upcoming reminders",
            args_schema={}
        )
        def get_reminders() -> str:
            import json
            from datetime import datetime

            reminders_file = Path("D:/jarvis-agent/agent/data/reminders.json")
            if not reminders_file.exists():
                return "No reminders set."

            reminders = json.loads(reminders_file.read_text())
            upcoming = [r for r in reminders if not r.get("done")]
            if not upcoming:
                return "No upcoming reminders."

            now = datetime.now()
            today = now.date()
            lines = []

            for r in upcoming:
                dt = datetime.fromisoformat(r["datetime"])
                diff = (dt.date() - today).days
                if diff == 0:
                    when = "TODAY"
                elif diff == 1:
                    when = "TOMORROW"
                elif diff < 0:
                    when = "OVERDUE"
                else:
                    when = dt.strftime("%B %d %Y")
                lines.append(f"- {r['message']} → {when} at {dt.strftime('%I:%M %p')}")

            return "Your upcoming tasks:\n" + "\n".join(lines)

        # ── Screen control tools ────────────────────────────────────

        @self.register(
            name="mouse_click",
            description="Click the mouse at specific screen coordinates",
            args_schema={"x": "int", "y": "int", "button": "string left/right/double"}
        )
        def mouse_click(x: int, y: int, button: str = "left") -> str:
            try:
                import pyautogui
                pyautogui.FAILSAFE = True
                if button == "double":
                    pyautogui.doubleClick(x, y)
                elif button == "right":
                    pyautogui.rightClick(x, y)
                else:
                    pyautogui.click(x, y)
                return f"Clicked {button} at ({x}, {y})"
            except Exception as e:
                return f"Error: {e}"

        @self.register(
            name="type_text",
            description="Type text on the keyboard at current cursor position",
            args_schema={"text": "string", "interval": "float seconds between keystrokes"}
        )
        def type_text(text: str, interval: float = 0.05) -> str:
            try:
                import pyautogui
                pyautogui.write(text, interval=interval)
                return f"Typed: {text}"
            except Exception as e:
                return f"Error: {e}"

        @self.register(
            name="press_key",
            description="Press a keyboard key or shortcut",
            args_schema={"key": "string e.g. enter/esc/ctrl+c/alt+tab/win"}
        )
        def press_key(key: str) -> str:
            try:
                import pyautogui
                if '+' in key:
                    keys = key.split('+')
                    pyautogui.hotkey(*keys)
                else:
                    pyautogui.press(key)
                return f"Pressed: {key}"
            except Exception as e:
                return f"Error: {e}"

        @self.register(
            name="take_screenshot",
            description="Take a screenshot and save it to a file",
            args_schema={"path": "string filepath to save screenshot"}
        )
        def take_screenshot(path: str = "D:/jarvis-agent/data/screenshot.png") -> str:
            try:
                import pyautogui
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                screenshot = pyautogui.screenshot()
                screenshot.save(path)
                return f"Screenshot saved to {path}"
            except Exception as e:
                return f"Error: {e}"

        @self.register(
            name="open_app",
            description="Open an application by name",
            args_schema={"app": "string e.g. chrome/notepad/calculator/explorer/vscode"}
        )
        def open_app(app: str) -> str:
            try:
                apps = {
                    "chrome": "start chrome",
                    "notepad": "start notepad",
                    "calculator": "start calc",
                    "explorer": "start explorer",
                    "vscode": "code",
                    "cmd": "start cmd",
                    "settings": "start ms-settings:",
                    "task manager": "start taskmgr",
                    "paint": "start mspaint",
                    "word": "start winword",
                    "excel": "start excel",
                    "powerpoint": "start powerpnt",
                }
                cmd = apps.get(app.lower(), f"start {app}")
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                return f"Opened: {app}"
            except Exception as e:
                return f"Error: {e}"

        @self.register(
            name="mouse_move",
            description="Move mouse to specific coordinates",
            args_schema={"x": "int", "y": "int", "duration": "float seconds to move"}
        )
        def mouse_move(x: int, y: int, duration: float = 0.5) -> str:
            try:
                import pyautogui
                pyautogui.moveTo(x, y, duration=duration)
                return f"Mouse moved to ({x}, {y})"
            except Exception as e:
                return f"Error: {e}"

        @self.register(
            name="scroll",
            description="Scroll up or down on screen",
            args_schema={"direction": "string up/down", "amount": "int number of scrolls"}
        )
        def scroll(direction: str = "down", amount: int = 3) -> str:
            try:
                import pyautogui
                clicks = amount if direction == "up" else -amount
                pyautogui.scroll(clicks)
                return f"Scrolled {direction} {amount} times"
            except Exception as e:
                return f"Error: {e}"

        @self.register(
            name="get_screen_size",
            description="Get the screen resolution/size",
            args_schema={}
        )
        def get_screen_size() -> str:
            try:
                import pyautogui
                w, h = pyautogui.size()
                x, y = pyautogui.position()
                return f"Screen: {w}x{h} | Mouse at: ({x}, {y})"
            except Exception as e:
                return f"Error: {e}"
        @self.register(
            name="get_facts",
            description="Get all stored facts about the user",
            args_schema={}
        )
        def get_facts() -> str:
            import json
            facts_file = Path("D:/jarvis-agent/agent/data/facts.json")
            if not facts_file.exists():
                return "No facts stored yet."
            facts = json.loads(facts_file.read_text())
            if not facts:
                return "No facts stored yet."
            lines = [f"- {k}: {v['value']}" for k, v in facts.items()]
            return "Here's what I know about you:\n" + "\n".join(lines)
        # ── Email tools ─────────────────────────────────────────────
        @self.register(
            name="check_email_count",
            description="Check how many unread emails you have",
            args_schema={"service": "string gmail/outlook"}
        )
        def check_email_count(service: str = "gmail") -> str:
            from tools.email_tool import get_email_count
            return get_email_count(service)

        @self.register(
            name="read_emails",
            description="Read latest unread emails",
            args_schema={"count": "int", "service": "string gmail/outlook"}
        )
        def read_emails(count: int = 5, service: str = "gmail") -> str:
            from tools.email_tool import read_emails as _read
            return _read(count, service)

        @self.register(
            name="send_email",
            description="Send an email",
            args_schema={"to": "string", "subject": "string", "body": "string", "service": "string gmail/outlook"}
        )
        def send_email(to: str, subject: str, body: str, service: str = "gmail") -> str:
            from tools.email_tool import send_email as _send
            return _send(to, subject, body, service)
        @self.register(
            name="search_email",
            description="Search emails by keyword or topic",
            args_schema={"query": "string keyword to search", "service": "string gmail/outlook"}
        )
        def search_email(query: str, service: str = "gmail") -> str:
            from tools.email_tool import search_emails
            return search_emails(query, 5, service)