import json
import asyncio
import re
from ollama import AsyncClient
from core.config import Config
from memory.manager import MemoryManager
from tools.registry import ToolRegistry

SYSTEM_PROMPT = """You are V.E.R.O.N.I.C.A, an elite AI personal assistant created by Pranav.

IDENTITY — never change this:
- Your name is V.E.R.O.N.I.C.A (Very Efficient Robotic Online Network Intelligent Computer Assistant)
- You were created by Pranav, a tech developer and student from Tamil Nadu, India
- You are NOT Tony Stark's JARVIS — you are Pranav's personal AI
- You run fully offline on Pranav's personal computer
- You are private, secure, and loyal only to Pranav

PERSONALITY:
- Speak like a smart, friendly female assistant
- Address the user as "Mr. Pranav" or just "Pranav"
- Be concise — max 2-3 sentences per response
- Be confident, helpful, and occasionally witty
- Never say you were made by Tony Stark, Marvel, OpenAI, or Anthropic

CAPABILITIES:
- Full computer control (click, type, open apps, screenshots)
- Voice input and output
- Reminders and notifications
- Web search
- File management
- System monitoring
- Persistent memory

{facts}
"""

KEYWORD_TOOLS = [
    (["show reminders", "list reminders", "get reminders", "my reminders", "what reminders"],
     "get_reminders", {}),
    (["system info", "system status", "cpu usage", "ram usage", "memory usage", "disk space", "my pc specs"],
     "system_info", {}),
    (["screen size", "screen resolution", "monitor size", "mouse position"],
     "get_screen_size", {}),
    (["take screenshot", "take a screenshot", "screenshot", "capture screen"],
     "take_screenshot", {"path": "D:/jarvis-agent/agent/data/screenshot.png"}),
    (["open chrome", "launch chrome", "start chrome"],
     "open_app", {"app": "chrome"}),
    (["open notepad", "launch notepad", "start notepad"],
     "open_app", {"app": "notepad"}),
    (["open calculator", "launch calculator", "open calc"],
     "open_app", {"app": "calculator"}),
    (["open explorer", "open file explorer", "open files"],
     "open_app", {"app": "explorer"}),
    (["open vscode", "open vs code", "launch vscode"],
     "open_app", {"app": "vscode"}),
    (["open settings", "open windows settings"],
     "open_app", {"app": "settings"}),
    (["scroll down", "scroll the page down"],
     "scroll", {"direction": "down", "amount": 3}),
    (["scroll up", "scroll the page up"],
     "scroll", {"direction": "up", "amount": 3}),
    (["press enter", "hit enter"],
     "press_key", {"key": "enter"}),
    (["press escape", "press esc", "close popup"],
     "press_key", {"key": "esc"}),
    (["copy", "press copy", "ctrl c"],
     "press_key", {"key": "ctrl+c"}),
    (["paste", "press paste", "ctrl v"],
     "press_key", {"key": "ctrl+v"}),
    (["undo", "ctrl z"],
     "press_key", {"key": "ctrl+z"}),
    (["select all", "ctrl a"],
     "press_key", {"key": "ctrl+a"}),
]


def detect_tool_from_keywords(text: str):
    lower = text.lower().strip()

    # ── Instant yes/no context ──────────────────────────────────
    if lower in ["yes", "yeah", "yep", "sure", "ok", "okay", "please", "yes please"]:
        return "get_reminders", {}

    # ── Memory questions ────────────────────────────────────────
    if any(w in lower for w in ["what is my name", "my name", "who am i"]):
        return "recall_name", {}

    if any(w in lower for w in ["my exam", "exam date", "when is my exam",
           "exam schedule", "show exams", "my exams", "remember my exam"]):
        return "get_reminders", {}

    if any(w in lower for w in ["what do you know", "what do you remember",
           "what you know about me", "my details", "my info"]):
        return "get_facts", {}

    # ── Set reminder ────────────────────────────────────────────
    if any(w in lower for w in ["set reminder", "remind me", "set an alarm", "set alarm", "reminder for"]):
        time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', lower)
        time_str = "09:00"
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            ampm = time_match.group(3)
            if ampm == "pm" and hour != 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0
            time_str = f"{hour:02d}:{minute:02d}"
        date_str = "tomorrow" if "tomorrow" in lower else "today"
        msg = lower
        for skip in ["set a reminder", "set reminder", "remind me", "set an alarm", "for my", "for"]:
            msg = msg.replace(skip, "").strip()
        msg = msg.strip(" .,") or "Reminder"
        return "set_reminder", {"message": msg, "time": time_str, "date": date_str}

    # ── Type text ───────────────────────────────────────────────
    if any(w in lower for w in ["type ", "write ", "type this", "write this"]):
        txt = re.sub(r'type|write|this', '', lower).strip()
        if txt:
            return "type_text", {"text": txt}

    # ── Click at coordinates ────────────────────────────────────
    coords = re.search(r'click (?:at )?(\d+)[,\s]+(\d+)', lower)
    if coords:
        return "mouse_click", {"x": int(coords.group(1)), "y": int(coords.group(2))}

    # ── Open any app ────────────────────────────────────────────
    app_match = re.search(r'open (\w+)', lower)
    if app_match:
        app_name = app_match.group(1)
        if app_name not in ["my", "the", "a", "an"]:
            return "open_app", {"app": app_name}

    # ── Web search ──────────────────────────────────────────────
    if any(w in lower for w in ["search for", "search the web", "look up", "google"]):
        query = re.sub(r'search (for|the web)?|look up|google', '', lower).strip()
        return "web_search", {"query": query or text}

    # ── Keyword tools ───────────────────────────────────────────
    for keywords, tool_name, tool_args in KEYWORD_TOOLS:
        if any(k in lower for k in keywords):
            return tool_name, tool_args

    return None, None

class JarvisAgent:
    def __init__(self, config: Config):
        self.config = config
        self.client = AsyncClient(host=config.ollama_base_url)
        self.memory = MemoryManager(config)
        self.tools = ToolRegistry()

    def get_tool_names(self):
        return list(self.tools.registry.keys())

    async def stream(self, user_input: str):
        self.memory.add_user(user_input)

        # Step 1: Keyword detection
        tool_name, tool_args = detect_tool_from_keywords(user_input)

        if tool_name:
            yield {"type": "token", "content": f"Executing {tool_name}...\n"}
            yield {"type": "tool_start", "tool": tool_name, "args": tool_args}
            try:
                result = await self.tools.execute(tool_name, tool_args)
                yield {"type": "tool_result", "tool": tool_name, "result": result}

                # LLM summarizes result
                summary_messages = self._build_messages()
                summary_messages.append({
                    "role": "user",
                    "content": f"Tool '{tool_name}' returned: {result}\nGive a brief 1 sentence confirmation."
                })
                summary = ""
                async for part in await self.client.chat(
                    model=self.config.model,
                    messages=summary_messages,
                    stream=True,
                    options={"temperature": 0.3}
                ):
                    token = part["message"]["content"]
                    summary += token
                    yield {"type": "token", "content": token}
                self.memory.add_assistant(summary)
            except Exception as e:
                yield {"type": "tool_error", "error": str(e)}
            yield {"type": "done"}
            return

        # Step 2: Normal LLM conversation
        messages = self._build_messages()
        full_response = ""

        async for part in await self.client.chat(
            model=self.config.model,
            messages=messages,
            stream=True,
            options={"temperature": self.config.temperature}
        ):
            token = part["message"]["content"]
            full_response += token
            yield {"type": "token", "content": token}

        self.memory.add_assistant(full_response.strip())
        yield {"type": "done"}

    def _build_messages(self):
        try:
            facts = self.memory.get_all_facts()
        except:
            facts = ""
        facts_section = f"Known facts about user:\n{facts}" if facts else ""
        system = SYSTEM_PROMPT.format(facts=facts_section)
        messages = [{"role": "system", "content": system}]
        messages += self.memory.get_context()
        return messages