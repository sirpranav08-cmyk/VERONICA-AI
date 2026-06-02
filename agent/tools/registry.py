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
                "created": datetime.now().isoformat(),
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

            lines = []
            for r in upcoming:
                dt = datetime.fromisoformat(r["datetime"])
                lines.append(f"- {r['message']} at {dt.strftime('%B %d %Y at %I:%M %p')}")
            return "\n".join(lines)

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