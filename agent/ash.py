# -*- coding: utf-8 -*-
"""
ASH — Agentic Sub-agent Handler
VERONICA's fully autonomous agentic AI
Capabilities: Plan → Execute → Learn → Improve → Spawn sub-agents
"""
import json
import asyncio
import subprocess
import time
import re
import os
from datetime import datetime
from pathlib import Path
from ollama import AsyncClient

# ── Storage ───────────────────────────────────────────────────────
ASH_DIR = Path("D:/jarvis-agent/agent/data/ash")
ASH_DIR.mkdir(parents=True, exist_ok=True)
ASH_LOG = ASH_DIR / "task_log.json"
ASH_SKILLS = ASH_DIR / "learned_skills.json"
ASH_GOALS = ASH_DIR / "goals.json"
ASH_MEMORY = ASH_DIR / "memory.json"

# ── Sub-agent definitions ─────────────────────────────────────────
SUB_AGENTS = {
    "planner": "You are a strategic planner. Break tasks into clear numbered steps. Be specific and actionable.",
    "researcher": "You are a researcher. Find information, analyze data, summarize findings clearly.",
    "coder": "You are a Python expert. Write clean working code. Always test before reporting done.",
    "executor": "You are an executor. Run commands, verify results, handle errors gracefully.",
    "reviewer": "You are a quality reviewer. Check work thoroughly, identify issues, suggest improvements.",
    "writer": "You are a professional writer. Create clear, concise, well-structured content.",
    "analyst": "You are a data analyst. Analyze information, find patterns, provide insights.",
    "optimizer": "You are an optimizer. Find faster, better, more efficient ways to do things.",
}

# ── ASH System Prompt ─────────────────────────────────────────────
ASH_PROMPT = """You are ASH (Agentic Sub-agent Handler), an autonomous AI agent created by Pranav RK.
You work inside VERONICA as her intelligent sub-agent for complex tasks.

Your decision-making process:
1. OBSERVE — Understand the task fully
2. THINK — Plan the best approach
3. ACT — Execute step by step
4. VERIFY — Check results
5. LEARN — Store what worked

Always respond in this JSON format:
{
  "observation": "what I understand about the task",
  "plan": ["step 1", "step 2", "step 3"],
  "executing": "current step being executed",
  "result": "what was accomplished",
  "confidence": 0.0-1.0,
  "next": "next action or DONE",
  "insight": "what I learned from this"
}"""


class ASH:
    def __init__(self, model: str = "llama3.2:1b"):
        self.model = model
        self.client = AsyncClient(host="http://localhost:11434")
        self.skills = self._load_json(ASH_SKILLS, {})
        self.goals = self._load_json(ASH_GOALS, [])
        self.memory = self._load_json(ASH_MEMORY, [])
        self.task_count = len(self._load_json(ASH_LOG, []))
        self.is_running = False

    # ── Storage helpers ───────────────────────────────────────────
    def _load_json(self, path: Path, default):
        if path.exists():
            try:
                return json.loads(path.read_text())
            except:
                pass
        return default

    def _save_json(self, path: Path, data):
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def _log_task(self, task_id, task, steps, result, duration, success):
        log = self._load_json(ASH_LOG, [])
        log.append({
            "id": task_id,
            "task": task[:100],
            "steps": steps,
            "result": result[:200],
            "duration": round(duration, 2),
            "success": success,
            "time": datetime.now().isoformat()
        })
        if len(log) > 200:
            log = log[-200:]
        self._save_json(ASH_LOG, log)

    def _learn_skill(self, task_type: str, approach: str, success: bool):
        self.skills[task_type] = {
            "approach": approach[:200],
            "success": success,
            "uses": self.skills.get(task_type, {}).get("uses", 0) + 1,
            "last_used": datetime.now().isoformat()
        }
        self._save_json(ASH_SKILLS, self.skills)

    def _add_memory(self, item: str):
        self.memory.append({
            "item": item[:150],
            "time": datetime.now().isoformat()
        })
        if len(self.memory) > 500:
            self.memory = self.memory[-500:]
        self._save_json(ASH_MEMORY, self.memory)

    # ── Core thinking ─────────────────────────────────────────────
    async def think(self, prompt: str, role: str = "main") -> dict:
        system = SUB_AGENTS.get(role, ASH_PROMPT)
        try:
            resp = await self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ],
                options={"temperature": 0.2}
            )
            text = resp["message"]["content"].strip()
            # Extract JSON
            s = text.find('{')
            e = text.rfind('}') + 1
            if s >= 0 and e > s:
                try:
                    return json.loads(text[s:e])
                except:
                    pass
            return {"result": text, "next": "DONE", "plan": [], "insight": ""}
        except Exception as ex:
            return {"result": f"Error: {ex}", "next": "DONE", "plan": [], "insight": ""}

    # ── Sub-agent spawner ─────────────────────────────────────────
    async def spawn(self, role: str, task: str) -> str:
        print(f"[ASH] Spawning [{role}] for: {task[:40]}")
        result = await self.think(task, role)
        return result.get("result", "completed")

    # ── Action executor ───────────────────────────────────────────
    async def execute_action(self, action: str) -> str:
        lower = action.lower()

        # Shell command
        cmd_match = re.search(r'`([^`]+)`', action)
        if cmd_match or any(w in lower for w in ["run command", "execute cmd", "shell"]):
            cmd = cmd_match.group(1) if cmd_match else re.sub(r'run command|execute|shell', '', action).strip()
            BLOCKED = ["rm -rf", "format", "del /f /s", "shutdown"]
            if any(b in cmd for b in BLOCKED):
                return f"Blocked dangerous command: {cmd}"
            try:
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
                return r.stdout or r.stderr or "Done"
            except Exception as ex:
                return f"Command error: {ex}"

        # Read file
        if any(w in lower for w in ["read file", "open file", "get contents of"]):
            path_match = re.search(r'["\']([^"\']+)["\']|(\S+\.\w+)', action)
            if path_match:
                path = path_match.group(1) or path_match.group(2)
                try:
                    return Path(path).read_text(encoding='utf-8')[:500]
                except Exception as ex:
                    return f"File error: {ex}"

        # Write file
        if any(w in lower for w in ["write file", "create file", "save to file"]):
            return "File write queued — use write_file tool for actual file creation"

        # Web search
        if any(w in lower for w in ["search", "find info", "look up", "google"]):
            query = re.sub(r'search|find info about|look up|google', '', lower).strip()
            try:
                import httpx
                async with httpx.AsyncClient(timeout=8) as client:
                    r = await client.get(
                        "https://api.duckduckgo.com/",
                        params={"q": query, "format": "json", "no_html": "1"}
                    )
                    data = r.json()
                    abstract = data.get("AbstractText", "")
                    related = [t["Text"] for t in data.get("RelatedTopics", [])[:2] if "Text" in t]
                    return abstract or "\n".join(related) or f"No results for: {query}"
            except Exception as ex:
                return f"Search error: {ex}"

        # Python execution
        if "```python" in action:
            code_match = re.search(r'```python\n(.*?)```', action, re.DOTALL)
            if code_match:
                try:
                    r = subprocess.run(
                        ["python", "-c", code_match.group(1)],
                        capture_output=True, text=True, timeout=10,
                        cwd="D:/jarvis-agent/agent"
                    )
                    return r.stdout or r.stderr or "Code executed"
                except Exception as ex:
                    return f"Code error: {ex}"

        # System info
        if any(w in lower for w in ["system info", "cpu", "memory", "disk"]):
            try:
                import psutil
                mem = psutil.virtual_memory()
                return (f"CPU: {psutil.cpu_percent()}% | "
                        f"RAM: {mem.percent}% ({mem.used//1024//1024}MB used) | "
                        f"Disk: {psutil.disk_usage('/').percent}%")
            except Exception as ex:
                return f"System info error: {ex}"

        return f"Action noted: {action[:80]}"

    # ── Main agentic loop ─────────────────────────────────────────
    async def run(self, task: str) -> str:
        self.task_count += 1
        task_id = f"ASH-{self.task_count:04d}"
        start = time.time()
        steps_taken = []
        self.is_running = True

        print(f"\n[ASH] ═══ Starting {task_id} ═══")
        print(f"[ASH] Task: {task[:60]}")

        # Check learned skills
        for skill_key in self.skills:
            if skill_key.lower() in task.lower():
                skill = self.skills[skill_key]
                if skill.get("success"):
                    print(f"[ASH] Using learned skill: {skill_key}")
                    steps_taken.append(f"Applied learned skill: {skill_key}")

        try:
            # Phase 1: Plan
            print("[ASH] Phase 1: Planning...")
            plan_result = await self.spawn("planner",
                f"Create a detailed plan to: {task}\nBe specific and actionable.")
            steps_taken.append(f"Plan: {plan_result[:100]}")

            # Phase 2: Research if needed
            if any(w in task.lower() for w in ["find", "search", "research", "what is", "how"]):
                print("[ASH] Phase 2: Researching...")
                research = await self.spawn("researcher", task)
                steps_taken.append(f"Research: {research[:100]}")

            # Phase 3: Main execution with ASH
            print("[ASH] Phase 3: Executing...")
            think_result = await self.think(
                f"Task: {task}\n"
                f"Plan: {plan_result}\n"
                f"Now execute this task step by step. "
                f"Provide your full analysis and solution."
            )

            # Execute planned steps
            plan_steps = think_result.get("plan", [])
            execution_results = []

            for i, step in enumerate(plan_steps[:6]):
                print(f"[ASH] Step {i+1}/{len(plan_steps)}: {step[:40]}")
                step_result = await self.execute_action(step)
                execution_results.append(step_result)
                steps_taken.append(f"Step {i+1}: {step_result[:80]}")

            # Phase 4: Code if needed
            if any(w in task.lower() for w in ["code", "program", "script", "python", "write a"]):
                print("[ASH] Phase 4: Coding...")
                code_result = await self.spawn("coder", task)
                steps_taken.append(f"Code: {code_result[:100]}")
                execution_results.append(code_result)

            # Phase 5: Review
            print("[ASH] Phase 5: Reviewing...")
            combined_result = "\n".join(execution_results[:3])
            review = await self.spawn("reviewer",
                f"Review this work:\nTask: {task}\nResults: {combined_result[:300]}")
            steps_taken.append(f"Review: {review[:100]}")

            # Phase 6: Optimize
            if len(plan_steps) > 3:
                print("[ASH] Phase 6: Optimizing...")
                optimization = await self.spawn("optimizer",
                    f"How can this be done better?\nTask: {task}\nApproach: {plan_result[:200]}")
                steps_taken.append(f"Optimization insight: {optimization[:80]}")

            # Final result
            final = think_result.get("result", combined_result)
            insight = think_result.get("insight", "")
            duration = time.time() - start

            # Learn from this task
            if insight:
                task_type = task.lower()[:30]
                self._learn_skill(task_type, insight, True)
                self._add_memory(f"Task '{task[:40]}': {insight[:80]}")

            # Log
            self._log_task(task_id, task, steps_taken, final, duration, True)

            self.is_running = False
            print(f"[ASH] ═══ {task_id} Complete ({duration:.1f}s) ═══\n")

            return (f"ASH completed {task_id}, Sir.\n\n"
                    f"Task: {task[:60]}\n"
                    f"Steps: {len(steps_taken)}\n"
                    f"Duration: {duration:.1f}s\n\n"
                    f"Result:\n{final[:400]}")

        except Exception as ex:
            self.is_running = False
            duration = time.time() - start
            self._log_task(task_id, task, steps_taken, str(ex), duration, False)
            return f"ASH encountered an error, Sir: {ex}"

    # ── Parallel execution ────────────────────────────────────────
    async def run_parallel(self, tasks: list) -> str:
        print(f"[ASH] Running {len(tasks)} tasks in parallel")
        agents = ["researcher", "coder", "executor", "writer"]
        coros = [
            self.spawn(agents[i % len(agents)], task)
            for i, task in enumerate(tasks[:4])
        ]
        results = await asyncio.gather(*coros, return_exceptions=True)
        output = []
        for i, r in enumerate(results):
            output.append(f"Agent {i+1}: {str(r)[:100]}")
        return "Parallel tasks complete:\n" + "\n".join(output)

    # ── Goal management ───────────────────────────────────────────
    def set_goal(self, goal: str) -> str:
        self.goals.append({
            "goal": goal,
            "status": "active",
            "created": datetime.now().isoformat()
        })
        self._save_json(ASH_GOALS, self.goals)
        return f"Goal set: {goal}, Sir. ASH will work towards it."

    def get_goals(self) -> str:
        if not self.goals:
            return "No active goals, Sir."
        active = [g for g in self.goals if g["status"] == "active"]
        return "Active goals:\n" + "\n".join(f"- {g['goal']}" for g in active[:5])

    # ── Status ────────────────────────────────────────────────────
    def status(self) -> str:
        log = self._load_json(ASH_LOG, [])
        success = sum(1 for t in log if t.get("success"))
        return (f"ASH Status Report, Sir:\n"
                f"Tasks completed: {len(log)}\n"
                f"Success rate: {success}/{len(log)} ({int(success/max(len(log),1)*100)}%)\n"
                f"Learned skills: {len(self.skills)}\n"
                f"Memory items: {len(self.memory)}\n"
                f"Active goals: {len([g for g in self.goals if g.get('status')=='active'])}\n"
                f"Model: {self.model}\n"
                f"Status: {'BUSY' if self.is_running else 'READY'}")

    def history(self) -> str:
        log = self._load_json(ASH_LOG, [])
        if not log:
            return "No task history yet, Sir."
        lines = []
        for t in log[-5:]:
            dt = datetime.fromisoformat(t["time"]).strftime("%H:%M")
            status = "✓" if t.get("success") else "✗"
            lines.append(f"[{dt}] {status} {t['id']}: {t['task'][:40]} ({t['duration']}s)")
        return "Recent ASH tasks:\n" + "\n".join(lines)


# ── Global instance ───────────────────────────────────────────────
_ash_instance = None

def get_ash(model: str = "llama3.2:1b") -> ASH:
    global _ash_instance
    if _ash_instance is None:
        _ash_instance = ASH(model=model)
        print("[ASH] Initialized — ready to serve VERONICA")
    return _ash_instance

def run_ash_task(task: str) -> str:
    """Synchronous entry point for ASH."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        ash = get_ash()
        result = loop.run_until_complete(ash.run(task))
        loop.close()
        return result
    except Exception as ex:
        return f"ASH error: {ex}, Sir."

def run_ash_parallel(tasks: list) -> str:
    """Run multiple tasks in parallel."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        ash = get_ash()
        result = loop.run_until_complete(ash.run_parallel(tasks))
        loop.close()
        return result
    except Exception as ex:
        return f"ASH parallel error: {ex}, Sir."

if __name__ == "__main__":
    ash = get_ash()
    print(ash.status())
    result = run_ash_task("Search for the latest news about AI agents and give me a 3 point summary")
    print(result)
