# -*- coding: utf-8 -*-
import json
import asyncio
import re
from ollama import AsyncClient
from core.config import Config
from memory.manager import MemoryManager
from tools.registry import ToolRegistry
import emotions
emotions.start()
# Face login on startup
import face_auth
face_auth.load_model()

try:
    from model_router import detect_model
    USE_ROUTER = True
except:
    USE_ROUTER = False

SYSTEM_PROMPT = """You are VERONICA,a self-developing AI assistant created by Pranav RK.

IDENTITY:
- You were built by Pranav RK
- You can write your own new tools and capabilities
- You learn and improve yourself over time
- You run fully offline on Pranav's Windows PC

SELF-DEVELOPMENT RULES:
- When asked to learn something new → use write_tool to create it
- When you make a mistake → analyze and fix it yourself
- When a tool fails → rewrite it better
- Always test new code before saving
- Keep backups before modifying yourself

CAPABILITIES:
- Voice, memory, email, screen control, reminders
- Self-coding — you can write new Python tools
- Self-testing — you verify your own code works
- Self-improving — you fix your own bugs

{facts}
"""

KEYWORD_TOOLS = [
    (["show reminders", "list reminders", "get reminders", "my reminders",
      "what reminders", "list the reminders", "show my reminders",
      "any reminders", "upcoming reminders", "check reminders",
      "reminder list", "my tasks", "pending tasks",
      "when is my", "when do i have", "leetcode contest",
      "my contest", "my exam", "my schedule", "today plan",
      "what is today", "today tasks"],
     "get_reminders", {}),
    (["system info", "system status", "cpu usage", "ram usage",
      "memory usage", "disk space", "my pc specs", "pc info"],
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
    (["scroll down"], "scroll", {"direction": "down", "amount": 3}),
    (["scroll up"], "scroll", {"direction": "up", "amount": 3}),
    (["press enter", "hit enter"], "press_key", {"key": "enter"}),
    (["press escape", "press esc"], "press_key", {"key": "esc"}),
    (["copy", "ctrl c"], "press_key", {"key": "ctrl+c"}),
    (["paste", "ctrl v"], "press_key", {"key": "ctrl+v"}),
    (["undo", "ctrl z"], "press_key", {"key": "ctrl+z"}),
    (["select all", "ctrl a"], "press_key", {"key": "ctrl+a"}),
    (["check email", "unread emails", "how many emails",
      "any emails", "my emails", "check my email", "new emails"],
     "check_email_count", {"service": "gmail"}),
    (["read emails", "show emails", "latest emails", "show my emails"],
     "read_emails", {"count": 5, "service": "gmail"}),
    (["battery", "battery status", "how much battery", "battery level"],
     "battery_status", {}),
    (["disk usage", "storage", "how much space", "disk space"],
     "get_disk_usage", {}),
    (["network info", "my ip", "ip address", "wifi info"],
     "network_info", {}),
    (["minimize all", "show desktop"], "minimize_all", {}),
    (["empty recycle", "clear recycle bin"], "empty_recycle_bin", {}),
    (["my bookings", "restaurant bookings", "show bookings"],
     "get_bookings", {}),
    (["what decisions", "autonomous decisions", "your decisions",
      "what have you done"], "get_decisions", {}),
]


def detect_tool_from_keywords(text):
    lower = text.lower().strip()
    # ── Full PC control ──────────────────────────────────────────
    if any(w in lower for w in ["shutdown", "shut down", "turn off pc",
                                  "turn off laptop"]):
        return "shutdown_pc", {"delay": 10}
    if any(w in lower for w in ["restart", "reboot"]):
        return "restart_pc", {"delay": 10}
    if "cancel shutdown" in lower:
        return "cancel_shutdown", {}
    if any(w in lower for w in ["sleep pc", "sleep laptop", "put to sleep"]):
        return "sleep_pc", {}
    if "hibernate" in lower:
        return "hibernate_pc", {}
    if any(w in lower for w in ["battery", "battery status", "battery level"]):
        return "battery_status", {}
    if any(w in lower for w in ["brightness"]):
        level = 50
        m = re.search(r'(\d+)', lower)
        if m: level = int(m.group(1))
        return "set_brightness", {"level": level}
    if any(w in lower for w in ["disable wifi", "wifi off", "turn off wifi"]):
        return "wifi_control", {"action": "disable"}
    if any(w in lower for w in ["enable wifi", "wifi on", "turn on wifi"]):
        return "wifi_control", {"action": "enable"}
    if any(w in lower for w in ["my ip", "ip address", "network info"]):
        return "network_info", {}
    if any(w in lower for w in ["ping"]):
        host = re.sub(r'ping', '', lower).strip() or "google.com"
        return "ping", {"host": host}
    if any(w in lower for w in ["list processes", "running apps",
                                  "what is running"]):
        return "list_processes", {}
    if any(w in lower for w in ["kill", "close process", "end task"]):
        name = re.sub(r'kill|process|close|end|task|app', '', lower).strip()
        if name:
            return "kill_process", {"name": name}
    if any(w in lower for w in ["disk usage", "storage", "how much space",
                                  "free space"]):
        return "get_disk_usage", {}
    if any(w in lower for w in ["empty recycle", "clear recycle bin"]):
        return "empty_recycle_bin", {}
    if any(w in lower for w in ["minimize all", "show desktop"]):
        return "minimize_all", {}
    if any(w in lower for w in ["close window", "close this"]):
        return "close_window", {}
    if any(w in lower for w in ["switch window", "alt tab", "next window"]):
        return "switch_window", {}
    if any(w in lower for w in ["snap left", "window left"]):
        return "window_snap_left", {}
    if any(w in lower for w in ["snap right", "window right"]):
        return "window_snap_right", {}
    if any(w in lower for w in ["get clipboard", "what is in clipboard",
                                  "read clipboard"]):
        return "get_clipboard", {}
    if any(w in lower for w in ["your decisions", "what did you decide",
                                  "autonomous", "what have you done",
                                  "show decisions", "your actions"]):
        return "show_decisions", {}
    if any(w in lower for w in ["open gmail", "open email", "check email"]):
        return "open_gmail", {}
    if any(w in lower for w in ["what have you learned", "your stats",
                                  "self learning", "how smart are you",
                                  "what do you know about my habits"]):
        return "self_dev_stats", {}

    if any(w in lower for w in ["learn to", "teach yourself",
                                  "generate tool", "create ability",
                                  "you can't do", "add ability"]):
        cap = re.sub(r'learn to|teach yourself|generate tool|create ability|you cant do|add ability', '', lower).strip()
        return "generate_tool", {"capability": cap or text}
    
    if any(w in lower for w in ["weather in", "weather of",
                                  "temperature in", "how is weather"]):
        city = re.sub(r'weather|temperature|in|of|what|is|the|how|like',
                     '', lower).strip() or "Coimbatore"
        return "get_weather", {"city": city}
    if any(w in lower for w in ["translate", "in tamil", "in hindi",
                                  "in french", "in japanese"]):
        lang = ("ta" if "tamil" in lower else
                "hi" if "hindi" in lower else
                "fr" if "french" in lower else
                "ja" if "japanese" in lower else "en")
        txt = re.sub(r'translate|in tamil|in hindi|in french|in japanese|this',
                    '', lower).strip()
        return "translate_text", {"text": txt or text, "target_lang": lang}
    if any(w in lower for w in ["search file", "find file", "where is"]):
        query = re.sub(r'search|find|file|where|is', '', lower).strip()
        return "search_files", {"query": query}
    # ── Full URL — highest priority ──────────────────────────────
    import re as _re
    full_url = _re.search(r'https?://\S+', text)
    if full_url:
        return "open_url", {"url": full_url.group()}
    
    # ── Face authentication ──────────────────────────────────────
    if any(w in lower for w in ["scan my face", "scan face", "face scan",
                                  "recognize me", "authenticate face",
                                  "face login", "scane my face", "scan me",
                                  "who am i", "identify me"]):
        return "face_login", {}

    if any(w in lower for w in ["register my face", "register face",
                                  "setup face", "add my face", "save my face"]):
        return "register_face", {"name": "Pranav"}

    if any(w in lower for w in ["who is there", "who do you see",
                                  "who is in front", "check camera"]):
        return "who_is_there", {}
    if any(w in lower for w in ["how are you", "how do you feel",
                                  "what is your mood", "are you okay",
                                  "how are you feeling", "your emotion"]):
        return "how_are_you", {}

    if any(w in lower for w in ["be happy", "cheer up", "be excited",
                                  "be calm", "be sad", "feel happy"]):
        emotion = re.search(r'happy|sad|excited|calm|angry|curious|tired|proud',
                           lower)
        if emotion:
            return "set_emotion", {"emotion": emotion.group()}
    
     # ── Face auth ─────────────────────────────────────────────────
    if any(w in lower for w in ["register my face", "register face",
                                  "setup face", "add my face"]):
        return "register_face", {"name": "Pranav"}

    if any(w in lower for w in ["face login", "authenticate face",
                                  "scan my face", "verify face"]):
        return "face_login", {}

    if any(w in lower for w in ["who is there", "who is in front",
                                  "who do you see", "camera"]):
        return "who_is_there", {}
     # ── Greetings — instant ──────────────────────────────────────
    if lower in ["hi", "hello", "hey", "hi veronica", "hello veronica",
                 "hey veronica", "good morning", "good afternoon",
                 "good evening", "good night", "greetings"]:
        return "speak_greeting", {}
    
    # ── Full control keywords ─────────────────────────────────────
    if any(w in lower for w in ["weather", "what is the weather",
                                  "how is the weather"]):
        city = re.sub(r'weather|what is|how is|the|in', '', lower).strip() or "Coimbatore"
        return "get_weather", {"city": city}

    if any(w in lower for w in ["send whatsapp", "whatsapp message",
                                  "message on whatsapp"]):
        return "whatsapp_send", {"phone": "+917358570817", "message": text}

    if any(w in lower for w in ["send email", "email to", "compose email"]):
        return "send_email", {"to": "", "subject": "Message from VERONICA", "body": text}

    if any(w in lower for w in ["download", "download file", "download from"]):
        url_m = re.search(r'https?://\S+', text)
        if url_m:
            return "download_file", {"url": url_m.group()}

    if any(w in lower for w in ["search youtube", "youtube", "play on youtube",
                                  "play from youtube", "play a song from youtube",
                                  "play song on youtube", "yotube", "you tube",
                                  "play on yt", "yt"]):
        # Remove only trigger words, keep song name
        query = lower
        for skip in ["search", "youtube", "yotube", "you tube", "play on",
                     "play from", "play a song from", "play song from",
                     "play", "from", "on", "yt", "a song", "song"]:
            query = query.replace(skip, "")
        query = query.strip(" .,") or "trending songs"
        return "youtube_search", {"query": query}
    
    if any(w in lower for w in ["translate", "translate this", "in tamil",
                                  "in hindi", "in french"]):
        lang = "ta" if "tamil" in lower else "hi" if "hindi" in lower else "fr" if "french" in lower else "en"
        txt = re.sub(r'translate|this|in tamil|in hindi|in french', '', lower).strip()
        return "translate_text", {"text": txt or text, "target_lang": lang}

    if any(w in lower for w in ["search file", "find file", "where is file"]):
        query = re.sub(r'search|find|file|where is', '', lower).strip()
        return "search_files", {"query": query}

    if any(w in lower for w in ["weather in", "weather of", "temperature in"]):
        city = re.sub(r'weather|temperature|in|of|what|is|the', '', lower).strip()
        return "get_weather", {"city": city or "Coimbatore"}
    
    # ── Creator ──────────────────────────────────────────────────
    if any(w in lower for w in ["i am your creator", "i am your crater",
                                  "i am your creater", "i made you",
                                  "i built you", "i created you",
                                  "your creator", "who created you"]):
        return "speak_creator", {}

    # ── Self intro ───────────────────────────────────────────────
    if any(w in lower for w in ["tell about yourself", "about yourself",
                                  "who are you", "introduce yourself",
                                  "what are you", "tell me about you"]):
        return "speak_intro", {}

    # ── Full form ────────────────────────────────────────────────
    if any(w in lower for w in ["full form of veronica", "what does veronica stand for",
                                  "full form", "expand veronica",
                                  "what is veronica"]):
        return "speak_fullform", {}

    # ── Knowledge questions — skip tools ─────────────────────────
    knowledge_keywords = [
        "what is", "explain", "tell me about", "how does", "define",
        "difference between", "describe", "data structure",
        "algorithm", "tree", "graph", "array", "linked list", "sorting",
        "what are", "how to", "why is", "when was"
    ]
    if any(w in lower for w in knowledge_keywords):
        return None, None

    # ── Instant context ──────────────────────────────────────────
    if lower in ["yes", "yeah", "yep", "sure", "ok", "okay", "please"]:
        return "get_reminders", {}

    # ── Memory ───────────────────────────────────────────────────
    if any(w in lower for w in ["what is my name", "my name", "who am i"]):
        return "recall_name", {}

    if any(w in lower for w in ["what do you know", "what do you remember",
                                  "my details", "my info", "know about me"]):
        return "get_facts", {}

    # ── Modes ────────────────────────────────────────────────────
    mode_map = {
        "study":        ["study mode", "activate study", "focus mode", "enable study"],
        "work":         ["work mode", "activate work", "office mode", "enable work"],
        "gaming":       ["gaming mode", "game mode", "activate gaming", "enable gaming"],
        "sleep":        ["sleep mode", "good night", "activate sleep", "go to sleep"],
        "presentation": ["presentation mode", "meeting mode", "activate presentation"],
        "performance":  ["performance mode", "boost mode", "boost llm", "max performance"],
        "fast":         ["fast mode", "speed mode", "quick mode", "instant response"],
        "night":        ["night mode", "activate night", "dark mode"],
    }
    for mode, keywords in mode_map.items():
        if any(k in lower for k in keywords):
            return "activate_mode", {"mode": mode}

    # ── PC control ───────────────────────────────────────────────
    if any(w in lower for w in ["shutdown", "shut down", "turn off pc"]):
        return "shutdown_pc", {"delay": 10}
    if any(w in lower for w in ["restart", "reboot"]):
        return "restart_pc", {"delay": 10}
    if "cancel shutdown" in lower:
        return "cancel_shutdown", {}
    if "hibernate" in lower:
        return "hibernate_pc", {}
    if any(w in lower for w in ["sleep pc", "put to sleep", "sleep laptop"]):
        return "sleep_pc", {}

    # ── Brightness ───────────────────────────────────────────────
    if "brightness" in lower:
        level = 75
        m = re.search(r'(\d+)', lower)
        if m:
            level = int(m.group(1))
        return "set_brightness", {"level": level}

    # ── WiFi ─────────────────────────────────────────────────────
    if any(w in lower for w in ["disable wifi", "turn off wifi", "wifi off"]):
        return "wifi_control", {"action": "disable"}
    if any(w in lower for w in ["enable wifi", "turn on wifi", "wifi on"]):
        return "wifi_control", {"action": "enable"}

    # ── Processes ────────────────────────────────────────────────
    if any(w in lower for w in ["list processes", "running apps", "what is running"]):
        return "list_processes", {}

    kill_match = re.search(r'kill\s+(\w+)', lower)
    if kill_match:
        return "kill_process", {"name": kill_match.group(1) + ".exe"}

    # ── Clipboard ────────────────────────────────────────────────
    if any(w in lower for w in ["get clipboard", "clipboard content", "what is in clipboard"]):
        return "get_clipboard", {}

    # ── Set reminder ─────────────────────────────────────────────
    if any(w in lower for w in ["set reminder", "remind me", "set an alarm",
                                  "set alarm", "reminder for", "notify me"]):
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
        if "monday" in lower:
            date_str = "monday"
        elif "tuesday" in lower:
            date_str = "tuesday"
        elif "wednesday" in lower:
            date_str = "wednesday"
        elif "thursday" in lower:
            date_str = "thursday"
        elif "friday" in lower:
            date_str = "friday"
        elif "saturday" in lower:
            date_str = "saturday"
        elif "sunday" in lower:
            date_str = "sunday"
        elif "tomorrow" in lower:
            date_str = "tomorrow"
        else:
            date_str = "today"
        msg = lower
        for skip in ["set a reminder", "set reminder", "remind me",
                     "set an alarm", "for my", "notify me", "for"]:
            msg = msg.replace(skip, "").strip()
        msg = msg.strip(" .,") or "Reminder"
        return "set_reminder", {"message": msg, "time": time_str, "date": date_str}

    # ── Type text ────────────────────────────────────────────────
    if any(w in lower for w in ["type ", "write this", "type this"]):
        txt = re.sub(r'type|write|this', '', lower).strip()
        if txt:
            return "type_text", {"text": txt}

    # ── Click ────────────────────────────────────────────────────
    coords = re.search(r'click (?:at )?(\d+)[,\s]+(\d+)', lower)
    if coords:
        return "mouse_click", {"x": int(coords.group(1)),
                               "y": int(coords.group(2))}

    # ── Open app ─────────────────────────────────────────────────
    app_match = re.search(r'open (\w+)', lower)
    if app_match:
        app_name = app_match.group(1)
        if app_name not in ["my", "the", "a", "an", "file"]:
            return "open_app", {"app": app_name}

    # ── Web search ───────────────────────────────────────────────
    if any(w in lower for w in ["search for", "search the web", "look up", "google"]):
        query = re.sub(r'search (for|the web)?|look up|google', '', lower).strip()
        return "web_search", {"query": query or text}

    # ── URL ──────────────────────────────────────────────────────
    url_match = re.search(r'(?:open|go to|browse|visit)\s+([\w\.-]+\.\w+)', lower)
    if url_match:
        return "open_url", {"url": url_match.group(1)}

    # ── Switch model ─────────────────────────────────────────────
    if any(w in lower for w in ["switch model", "change model", "use mistral",
                                  "use llama", "change llm", "switch llm"]):
        for m in ["mistral", "llama3.2", "phi3", "tinyllama", "gemma2", "deepseek"]:
            if m in lower:
                return "switch_model", {"model": m}

    # ── Restaurant booking ───────────────────────────────────────
    if any(w in lower for w in ["book a table", "book table", "reserve table",
                                  "restaurant booking", "book restaurant"]):
        return "book_restaurant", {"text": text}

    # ── Email search ─────────────────────────────────────────────
    if "email" in lower and any(w in lower for w in ["from", "about", "any", "search"]):
        words = re.sub(r'email|any|there|is|search|for|from|about', '', lower).strip()
        if words:
            return "search_email", {"query": words}

    # ── Keyword tools ────────────────────────────────────────────
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
    
        # Keyword detection first
        tool_name, tool_args = detect_tool_from_keywords(user_input)

        if tool_name:
            # Instant responses
            if tool_name == "speak_creator":
                reply = ("Yes, I know! You are Pranav RK, my creator. "
                         "Everything I am, I owe to you, Sir.")
                yield {"type": "token", "content": reply}
                self.memory.add_assistant(reply)
                yield {"type": "done"}
                return
            if tool_name == "speak_greeting":
                from datetime import datetime
                h = datetime.now().hour
                g = "Good morning" if h < 12 else "Good afternoon" if h < 18 else "Good evening"
                reply = f"{g}, Sir. All systems online. How can I assist you?"
                yield {"type": "token", "content": reply}
                self.memory.add_assistant(reply)
                yield {"type": "done"}
                return

            if tool_name == "speak_status":
                reply = "All systems nominal, Sir. 8 LLMs loaded, memory active, tools ready."
                yield {"type": "token", "content": reply}
                self.memory.add_assistant(reply)
                yield {"type": "done"}
                return

            if tool_name == "speak_intro":
                reply = ("I am VERONICA, Very Efficient Robotic Online "
                         "Network Intelligent Computer Assistant. "
                         "Created by Pranav RK, running fully offline on your PC. "
                         "I can hear you, speak with emotions, control your screen, "
                         "manage emails, set reminders, and remember everything. "
                         "Always here for you, Sir.")
                yield {"type": "token", "content": reply}
                self.memory.add_assistant(reply)
                yield {"type": "done"}
                return

            if tool_name == "speak_fullform":
                reply = ("VERONICA stands for Very Efficient Robotic "
                         "Online Network Intelligent Computer Assistant, Sir.")
                yield {"type": "token", "content": reply}
                self.memory.add_assistant(reply)
                yield {"type": "done"}
                return

            if tool_name == "recall_name":
                name = self.memory.recall_fact('user_name') or "Pranav"
                reply = f"Your name is {name}, Sir."
                yield {"type": "token", "content": reply}
                self.memory.add_assistant(reply)
                yield {"type": "done"}
                return

            # Tool execution
            yield {"type": "tool_start", "tool": tool_name, "args": tool_args}
            try:
                result = await self.tools.execute(tool_name, tool_args)
                yield {"type": "tool_result", "tool": tool_name, "result": result}
                yield {"type": "token", "content": str(result)}
                self.memory.add_assistant(str(result))
            except Exception as e:
                err = f"Tool error: {str(e)}, Sir."
                yield {"type": "tool_error", "error": err}
                yield {"type": "token", "content": err}
            yield {"type": "done"}
            return

        # LLM conversation
        selected_model = detect_model(user_input) if USE_ROUTER else self.config.model
        if USE_ROUTER and selected_model != self.config.model:
            yield {"type": "model_switch", "model": selected_model}

        try:
            messages = self._build_messages()
            full_response = ""

            async for part in await self.client.chat(
                model=selected_model,
                messages=messages,
                stream=True,
                options={"temperature": self.config.temperature}
            ):
                token = part["message"]["content"]
                full_response += token
                yield {"type": "token", "content": token}

            # Add emotional coloring
            user_emotion = emotions.detect_user_emotion(user_input)
            emotional_response = emotions.add_emotion_to_response(
                full_response.strip(), "task", user_emotion
            )
            # Send emotion state to UI
            emotion_state = emotions.get_current_emotion()
            yield {"type": "emotion", "state": emotion_state}
            self.memory.add_assistant(emotional_response.strip())
            yield {"type": "done"}
        except Exception as e:
            print(f"[VERONICA] LLM Error: {e}")
            err = str(e)
            if "connection" in err.lower():
                reply = "Ollama is not running, Sir. Please start Ollama first."
            elif "model" in err.lower():
                reply = f"Model '{selected_model}' not found, Sir. Run: ollama pull {selected_model}"
            else:
                reply = f"I encountered an error, Sir: {err[:100]}"
            yield {"type": "token", "content": reply}
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