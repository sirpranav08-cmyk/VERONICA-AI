"""
VERONICA Self-Development Engine
- Learns from conversations
- Auto-fixes errors
- Writes new tools
- Predicts user needs
"""
import json
import time
import threading
import subprocess
import os
import re
from pathlib import Path
from datetime import datetime
from collections import Counter

# ── PATHS ─────────────────────────────────────────────────────────
DATA_DIR = Path("D:/jarvis-agent/agent/data")
LEARN_FILE = DATA_DIR / "learned_patterns.json"
ERROR_LOG = DATA_DIR / "error_log.json"
USAGE_LOG = DATA_DIR / "usage_log.json"
NEW_TOOLS = DATA_DIR / "new_tools.py"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── USAGE TRACKER ─────────────────────────────────────────────────
usage_data = {"commands": [], "errors": [], "patterns": {}, "predictions": []}

def load_data():
    global usage_data
    if USAGE_LOG.exists():
        try:
            usage_data = json.loads(USAGE_LOG.read_text())
        except:
            pass

def save_data():
    USAGE_LOG.write_text(json.dumps(usage_data, indent=2))

def log_command(cmd: str, tool: str, success: bool, response: str):
    """Log every command VERONICA receives."""
    entry = {
        "cmd": cmd,
        "tool": tool,
        "success": success,
        "response": response[:100],
        "time": datetime.now().isoformat(),
        "hour": datetime.now().hour,
        "day": datetime.now().strftime("%A")
    }
    usage_data["commands"].append(entry)
    # Keep last 1000
    if len(usage_data["commands"]) > 1000:
        usage_data["commands"] = usage_data["commands"][-1000:]
    save_data()

def log_error(error: str, context: str):
    """Log errors for auto-fix."""
    entry = {
        "error": error,
        "context": context,
        "time": datetime.now().isoformat(),
        "fixed": False
    }
    usage_data["errors"].append(entry)
    if len(usage_data["errors"]) > 200:
        usage_data["errors"] = usage_data["errors"][-200:]
    save_data()

# ── PATTERN LEARNING ──────────────────────────────────────────────
def learn_patterns():
    """Analyze usage patterns and learn preferences."""
    cmds = [c["cmd"].lower() for c in usage_data["commands"]]
    if len(cmds) < 10:
        return {}

    # Most used commands
    words = []
    for cmd in cmds:
        words.extend(cmd.split())
    common = Counter(words).most_common(20)

    # Time patterns
    hours = [c["hour"] for c in usage_data["commands"]]
    peak_hour = Counter(hours).most_common(1)[0][0] if hours else 9

    # Day patterns
    days = [c["day"] for c in usage_data["commands"]]
    peak_day = Counter(days).most_common(1)[0][0] if days else "Monday"

    # Tool usage
    tools = [c["tool"] for c in usage_data["commands"] if c.get("tool")]
    fav_tools = Counter(tools).most_common(5)

    patterns = {
        "common_words": common,
        "peak_hour": peak_hour,
        "peak_day": peak_day,
        "favorite_tools": fav_tools,
        "total_commands": len(cmds)
    }
    usage_data["patterns"] = patterns
    save_data()
    return patterns

# ── PREDICTION ENGINE ─────────────────────────────────────────────
def predict_next_command() -> str:
    """Predict what user might need next."""
    now = datetime.now()
    hour = now.hour
    day = now.strftime("%A")
    cmds = usage_data["commands"]

    if not cmds:
        return None

    # Find commands used at this hour on this day
    similar = [c["cmd"] for c in cmds
               if c.get("hour") == hour and c.get("day") == day]

    if similar:
        most_common = Counter(similar).most_common(1)[0][0]
        return most_common

    # Find commands used at this hour
    hourly = [c["cmd"] for c in cmds if c.get("hour") == hour]
    if hourly:
        return Counter(hourly).most_common(1)[0][0]

    return None

def get_proactive_suggestion() -> str:
    """Generate proactive suggestion based on time and patterns."""
    now = datetime.now()
    hour = now.hour
    patterns = usage_data.get("patterns", {})

    suggestions = []

    # Morning routine
    if 6 <= hour <= 9:
        suggestions.append("Good morning, Sir. Shall I show your tasks for today?")

    # Work hours
    elif 9 <= hour <= 17:
        fav = patterns.get("favorite_tools", [])
        if fav:
            top_tool = fav[0][0] if fav else None
            if top_tool == "open_url":
                suggestions.append("Sir, shall I open your usual work pages?")

    # Evening
    elif 17 <= hour <= 20:
        suggestions.append("Sir, your work day is ending. Shall I show a summary?")

    # Night
    elif hour >= 22:
        suggestions.append("Sir, it is late. Shall I activate sleep mode?")

    return suggestions[0] if suggestions else None

# ── AUTO-FIX ENGINE ───────────────────────────────────────────────
def analyze_errors() -> list:
    """Analyze errors and suggest fixes."""
    errors = usage_data.get("errors", [])
    unfixed = [e for e in errors if not e.get("fixed")]

    fixes = []
    for error in unfixed[-5:]:
        err_str = error.get("error", "")
        fix = None

        if "cannot find module" in err_str.lower():
            module = re.search(r"'(\w+)'", err_str)
            if module:
                fix = {
                    "error": err_str,
                    "fix": f"pip install {module.group(1)}",
                    "action": "install_package",
                    "package": module.group(1)
                }

        elif "connection refused" in err_str.lower():
            fix = {
                "error": err_str,
                "fix": "Restart Ollama service",
                "action": "restart_ollama"
            }

        elif "permission denied" in err_str.lower():
            fix = {
                "error": err_str,
                "fix": "Run as administrator",
                "action": "elevate"
            }

        elif "not found" in err_str.lower():
            fix = {
                "error": err_str,
                "fix": "Check file path",
                "action": "check_path"
            }

        if fix:
            fixes.append(fix)

    return fixes

def auto_fix_error(fix: dict) -> str:
    """Apply automatic fix."""
    action = fix.get("action")

    if action == "install_package":
        pkg = fix.get("package")
        result = subprocess.run(
            [".venv/Scripts/pip", "install", pkg],
            cwd="D:/jarvis-agent/agent",
            capture_output=True, text=True
        )
        return f"Installed {pkg}: {result.returncode == 0}"

    elif action == "restart_ollama":
        subprocess.Popen(["ollama", "serve"],
                        creationflags=subprocess.CREATE_NO_WINDOW)
        return "Restarted Ollama"

    return f"Fix applied: {fix.get('fix')}"

# ── TOOL WRITER ───────────────────────────────────────────────────
def write_new_tool(tool_name: str, description: str, code: str) -> str:
    """Write a new tool to the tools file."""
    tool_code = f'''
# Auto-generated tool: {tool_name}
# Created: {datetime.now().isoformat()}
# Description: {description}

def {tool_name}(**kwargs) -> str:
    try:
{chr(10).join("        " + line for line in code.splitlines())}
    except Exception as e:
        return f"Error in {tool_name}: {{e}}"
'''
    # Append to new tools file
    with open(NEW_TOOLS, 'a') as f:
        f.write(tool_code)

    return f"New tool '{tool_name}' written, Sir. Restart to activate."

def generate_tool_from_failed_command(cmd: str) -> str:
    """When VERONICA can't do something, write a tool for it."""
    # Use Ollama to generate the tool code
    import requests
    prompt = f"""Write a Python function that can: {cmd}
Return ONLY the Python function body (no def line, just the code inside).
Use subprocess, os, or pyautogui. Keep it simple and working on Windows."""

    try:
        r = requests.post("http://localhost:11434/api/generate",
                         json={"model": "codellama:latest",
                               "prompt": prompt,
                               "stream": False},
                         timeout=30)
        code = r.json().get("response", "pass")
        tool_name = cmd.lower().replace(" ", "_")[:30]
        return write_new_tool(tool_name, cmd, code)
    except Exception as e:
        return f"Could not generate tool: {e}"

# ── SELF IMPROVEMENT LOOP ─────────────────────────────────────────
def self_improve_loop():
    """Background loop that continuously improves VERONICA."""
    print("[SelfDev] Self-improvement engine started")
    load_data()

    while True:
        try:
            # Every 5 minutes — learn patterns
            learn_patterns()

            # Check for errors to fix
            fixes = analyze_errors()
            for fix in fixes[:2]:
                print(f"[SelfDev] Auto-fixing: {fix['fix']}")
                auto_fix_error(fix)

            # Get prediction
            pred = predict_next_command()
            if pred:
                usage_data["predictions"] = [pred]
                save_data()

        except Exception as e:
            print(f"[SelfDev] Error: {e}")

        time.sleep(300)  # Every 5 minutes

def start():
    """Start self-development engine."""
    t = threading.Thread(target=self_improve_loop, daemon=True)
    t.start()
    return t

def get_stats() -> dict:
    """Get self-development statistics."""
    load_data()
    patterns = learn_patterns()
    return {
        "total_commands": len(usage_data.get("commands", [])),
        "total_errors": len(usage_data.get("errors", [])),
        "patterns": patterns,
        "prediction": predict_next_command(),
        "suggestion": get_proactive_suggestion()
    }

if __name__ == "__main__":
    load_data()
    stats = get_stats()
    print(json.dumps(stats, indent=2, default=str))