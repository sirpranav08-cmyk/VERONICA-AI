"""
VERONICA Complete Agentic AI Engine
- Goal decomposition
- Multi-step planning
- Tool execution
- Self reflection
- Memory across tasks
- Error recovery
- Parallel execution
- Task queue
"""
import json
import asyncio
import re
import time
import threading
from datetime import datetime
from pathlib import Path
from collections import deque

DATA_DIR = Path("D:/jarvis-agent/agent/data")
TASKS_FILE = DATA_DIR / "agentic_tasks.json"
MEMORY_FILE = DATA_DIR / "agentic_memory.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── TASK STATES ───────────────────────────────────────────────────
TASK_PENDING   = "pending"
TASK_PLANNING  = "planning"
TASK_RUNNING   = "running"
TASK_DONE      = "done"
TASK_FAILED    = "failed"
TASK_RETRYING  = "retrying"

# ── AGENTIC MEMORY ────────────────────────────────────────────────
class AgenticMemory:
    def __init__(self):
        self.short_term = deque(maxlen=20)
        self.long_term = {}
        self.load()

    def load(self):
        if MEMORY_FILE.exists():
            try:
                data = json.loads(MEMORY_FILE.read_text())
                self.long_term = data.get("long_term", {})
            except: pass

    def save(self):
        MEMORY_FILE.write_text(json.dumps({
            "long_term": self.long_term
        }, indent=2))

    def remember(self, key: str, value):
        self.long_term[key] = {
            "value": value,
            "time": datetime.now().isoformat()
        }
        self.save()

    def recall(self, key: str):
        return self.long_term.get(key, {}).get("value")

    def add_context(self, item: dict):
        self.short_term.append(item)

    def get_context(self) -> list:
        return list(self.short_term)

# ── GOAL PLANNER ──────────────────────────────────────────────────
class GoalPlanner:
    def __init__(self, config):
        self.config = config

    async def decompose(self, goal: str) -> list:
        """Break goal into executable steps."""
        from ollama import AsyncClient
        client = AsyncClient(host=self.config.ollama_base_url)

        available_tools = [
            "open_url", "web_search", "send_email", "whatsapp_send",
            "take_screenshot", "run_shell", "write_file", "read_file",
            "open_app", "get_weather", "translate_text", "youtube_search",
            "system_info", "get_reminders", "set_reminder", "play_spotify",
            "lock_screen", "volume_control", "get_disk_usage", "network_info",
            "take_screenshot", "list_processes", "kill_process", "battery_status",
            "get_clipboard", "set_clipboard", "search_files", "open_folder",
            "activate_mode", "shutdown_pc", "restart_pc", "set_brightness",
            "mouse_click", "type_text", "press_key", "scroll", "minimize_all"
        ]

        prompt = f"""You are VERONICA's task planner. Break this goal into steps.

Goal: {goal}

Available tools: {", ".join(available_tools)}

Rules:
- Max 5 steps
- Each step must use ONE tool
- Args must match the tool
- Be specific and actionable

Return ONLY valid JSON array:
[
  {{
    "step": 1,
    "tool": "tool_name",
    "args": {{"key": "value"}},
    "description": "what this does",
    "depends_on": []
  }}
]"""

        try:
            resp = await client.chat(
                model="llama3.2:1b",
                messages=[{"role": "user", "content": prompt}],
                stream=False,
                options={"temperature": 0.1, "num_predict": 500}
            )
            text = resp["message"]["content"].strip()
            match = re.search(r'\[.*?\]', text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            print(f"[Planner] Error: {e}")
        return []

    async def replan(self, goal: str, failed_step: dict,
                    error: str) -> list:
        """Replan after a step fails."""
        from ollama import AsyncClient
        client = AsyncClient(host=self.config.ollama_base_url)

        prompt = f"""Goal: {goal}
Step that failed: {json.dumps(failed_step)}
Error: {error}

Create a NEW single step to recover from this failure.
Return ONLY JSON: {{"tool": "name", "args": {{}}, "description": "..."}}"""

        try:
            resp = await client.chat(
                model="tinyllama",
                messages=[{"role": "user", "content": prompt}],
                stream=False,
                options={"temperature": 0.2}
            )
            text = resp["message"]["content"].strip()
            match = re.search(r'\{.*?\}', text, re.DOTALL)
            if match:
                step = json.loads(match.group())
                step["step"] = failed_step.get("step", 99)
                step["depends_on"] = []
                return [step]
        except: pass
        return []

# ── STEP EXECUTOR ─────────────────────────────────────────────────
class StepExecutor:
    def __init__(self, tools):
        self.tools = tools
        self.results = {}

    async def execute(self, step: dict) -> dict:
        """Execute a single step with retry."""
        tool = step.get("tool") or step.get("action")
        args = step.get("args", {})
        step_num = step.get("step", 0)
        desc = step.get("description", tool)

        print(f"[Executor] Step {step_num}: {desc}")

        for attempt in range(3):
            try:
                result = await self.tools.execute(tool, args)
                self.results[step_num] = result
                return {
                    "step": step_num,
                    "tool": tool,
                    "description": desc,
                    "result": result,
                    "success": True,
                    "attempts": attempt + 1
                }
            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(1)
                    continue
                return {
                    "step": step_num,
                    "tool": tool,
                    "description": desc,
                    "result": str(e),
                    "success": False,
                    "attempts": attempt + 1
                }

    def get_result(self, step_num: int) -> str:
        return self.results.get(step_num, "")

# ── REFLECTOR ─────────────────────────────────────────────────────
class Reflector:
    def __init__(self, config):
        self.config = config

    async def reflect(self, goal: str, steps: list,
                     results: list) -> str:
        """Reflect on what was done and summarize."""
        from ollama import AsyncClient
        client = AsyncClient(host=self.config.ollama_base_url)

        done = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]

        prompt = f"""Goal: {goal}
Completed {len(done)}/{len(results)} steps.
Results summary: {json.dumps([{
    "step": r["step"],
    "action": r["description"],
    "success": r["success"]
} for r in results], indent=2)}

Write a 2 sentence summary addressing user as Sir.
Be honest about what worked and what didn't."""

        try:
            resp = await client.chat(
                model="tinyllama",
                messages=[{"role": "user", "content": prompt}],
                stream=False,
                options={"temperature": 0.3, "num_predict": 100}
            )
            return resp["message"]["content"].strip()
        except:
            if failed:
                return (f"Completed {len(done)} of {len(results)} steps, Sir. "
                       f"{len(failed)} step(s) encountered issues.")
            return f"All {len(done)} steps completed successfully, Sir."

    async def learn(self, goal: str, results: list,
                   memory: AgenticMemory):
        """Learn from this task execution."""
        # Remember successful tool combinations
        successful_tools = [r["tool"] for r in results if r.get("success")]
        if successful_tools:
            pattern_key = f"pattern_{goal[:20].replace(' ','_')}"
            memory.remember(pattern_key, {
                "goal": goal,
                "tools": successful_tools,
                "success_rate": len([r for r in results
                                   if r.get("success")]) / len(results)
            })

# ── TASK ──────────────────────────────────────────────────────────
class AgenticTask:
    def __init__(self, goal: str):
        self.id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.goal = goal
        self.status = TASK_PENDING
        self.steps = []
        self.results = []
        self.created = datetime.now().isoformat()
        self.completed = None
        self.summary = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "goal": self.goal,
            "status": self.status,
            "steps": len(self.steps),
            "completed_steps": len([r for r in self.results
                                   if r.get("success")]),
            "created": self.created,
            "completed": self.completed,
            "summary": self.summary
        }

# ── MAIN AGENTIC MANAGER ──────────────────────────────────────────
class AgenticManager:
    def __init__(self, config, tools):
        self.config = config
        self.tools = tools
        self.planner = GoalPlanner(config)
        self.executor = StepExecutor(tools)
        self.reflector = Reflector(config)
        self.memory = AgenticMemory()
        self.task_queue = asyncio.Queue()
        self.task_history = []
        self.active_task = None

    async def run_goal(self, goal: str, callback=None) -> str:
        """Execute a complete agentic goal."""
        task = AgenticTask(goal)
        self.active_task = task
        self.task_history.append(task)

        try:
            # ── PHASE 1: PLANNING ─────────────────────────────────
            task.status = TASK_PLANNING
            if callback:
                await callback({
                    "type": "agentic_start",
                    "goal": goal,
                    "task_id": task.id
                })
                await callback({
                    "type": "token",
                    "content": f"🧠 Planning how to: {goal}\n"
                })

            steps = await self.planner.decompose(goal)

            if not steps:
                # Fallback — try simple execution
                task.status = TASK_FAILED
                return f"I could not plan steps for that goal, Sir. Please be more specific."

            task.steps = steps
            task.status = TASK_RUNNING

            if callback:
                await callback({
                    "type": "token",
                    "content": f"📋 {len(steps)} steps planned. Executing...\n\n"
                })

            # ── PHASE 2: EXECUTION ────────────────────────────────
            executor = StepExecutor(self.tools)
            results = []

            for step in steps:
                step_num = step.get("step", 0)
                desc = step.get("description", "")

                if callback:
                    await callback({
                        "type": "token",
                        "content": f"⚡ Step {step_num}: {desc}\n"
                    })

                result = await executor.execute(step)
                results.append(result)

                if callback:
                    status = "✅" if result["success"] else "❌"
                    await callback({
                        "type": "token",
                        "content": f"{status} {result.get('result', '')[:80]}\n"
                    })

                # If step failed — try to recover
                if not result["success"] and step_num < len(steps):
                    recovery = await self.planner.replan(
                        goal, step, result["result"])
                    if recovery:
                        if callback:
                            await callback({
                                "type": "token",
                                "content": "🔄 Trying recovery step...\n"
                            })
                        rec_result = await executor.execute(recovery[0])
                        results.append(rec_result)

                await asyncio.sleep(0.5)

            task.results = results

            # ── PHASE 3: REFLECTION ───────────────────────────────
            if callback:
                await callback({
                    "type": "token",
                    "content": "\n🔍 Reflecting on results...\n"
                })

            summary = await self.reflector.reflect(goal, steps, results)
            await self.reflector.learn(goal, results, self.memory)

            task.status = TASK_DONE
            task.completed = datetime.now().isoformat()
            task.summary = summary

            # Add context to memory
            self.memory.add_context({
                "goal": goal,
                "success": len([r for r in results if r.get("success")]),
                "total": len(results),
                "time": task.completed
            })

            if callback:
                await callback({"type": "done"})

            return summary

        except Exception as e:
            task.status = TASK_FAILED
            print(f"[Agentic] Fatal error: {e}")
            if callback:
                await callback({"type": "done"})
            return f"Agentic task failed, Sir: {str(e)[:100]}"

        finally:
            self.active_task = None
            self._save_history()

    def _save_history(self):
        try:
            data = [t.to_dict() for t in self.task_history[-20:]]
            TASKS_FILE.write_text(json.dumps(data, indent=2))
        except: pass

    def get_history(self) -> list:
        return [t.to_dict() for t in self.task_history[-10:]]

    def get_active_task(self):
        if self.active_task:
            return self.active_task.to_dict()
        return None

    def get_memory_stats(self) -> dict:
        return {
            "long_term_memories": len(self.memory.long_term),
            "short_term_context": len(self.memory.get_context()),
            "tasks_completed": len([t for t in self.task_history
                                   if t.status == TASK_DONE]),
            "tasks_failed": len([t for t in self.task_history
                                if t.status == TASK_FAILED])
        }

# ── GOAL DETECTOR ─────────────────────────────────────────────────
AGENTIC_TRIGGERS = [
    "find me", "research", "book a", "plan a",
    "help me", "i need you to", "organize",
    "create a plan", "set up", "do everything",
    "handle", "manage", "automatically",
    "complete task", "full task", "step by step",
    "can you do", "take care of",
]

AGENTIC_EXCLUDE = [
    "hi", "hello", "how are you", "what is",
    "who are you", "open", "play", "show",
    "volume", "lock", "shutdown", "restart"
]

def is_agentic_goal(text: str) -> bool:
    """Detect if this needs agentic execution."""
    lower = text.lower()
    if any(e in lower for e in AGENTIC_EXCLUDE):
        return False
    has_trigger = any(t in lower for t in AGENTIC_TRIGGERS)
    word_count = len(text.split())
    return has_trigger and word_count > 6