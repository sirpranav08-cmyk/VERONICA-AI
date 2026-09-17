"""
VERONICA Complete Agentic AI Engine v2.0
Production-grade autonomous agent with:
- Smart goal detection
- Pattern-based + LLM planning
- Multi-step execution
- Error recovery
- Self reflection
- Learning from outcomes
"""
import json
import asyncio
import re
import time
from datetime import datetime
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path("D:/jarvis-agent/agent/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
TASKS_FILE  = DATA_DIR / "agentic_tasks.json"
MEMORY_FILE = DATA_DIR / "agentic_memory.json"

# ── TASK STATES ───────────────────────────────────────────────────
PENDING  = "pending"
PLANNING = "planning"
RUNNING  = "running"
DONE     = "done"
FAILED   = "failed"

# ── AGENTIC MEMORY ────────────────────────────────────────────────
class AgenticMemory:
    def __init__(self):
        self.short_term = []
        self.long_term  = {}
        self.load()

    def load(self):
        if MEMORY_FILE.exists():
            try:
                d = json.loads(MEMORY_FILE.read_text())
                self.long_term = d.get("long_term", {})
            except: pass

    def save(self):
        MEMORY_FILE.write_text(json.dumps(
            {"long_term": self.long_term}, indent=2))

    def remember(self, key: str, value):
        self.long_term[key] = {
            "value": value,
            "time": datetime.now().isoformat()
        }
        self.save()

    def recall(self, key: str):
        return self.long_term.get(key, {}).get("value")

    def add(self, item: dict):
        self.short_term.append(item)
        if len(self.short_term) > 20:
            self.short_term = self.short_term[-20:]

# ── SMART PLANNER ─────────────────────────────────────────────────
class SmartPlanner:
    def __init__(self, config):
        self.config = config

    def _make_step(self, n, tool, args, desc):
        return {"step": n, "tool": tool, "args": args, "description": desc}

    async def plan(self, goal: str) -> list:
        """Generate execution plan for a goal."""
        lower = goal.lower()
                # ── ONLINE COURSE ─────────────────────────────────────────
        if any(w in lower for w in ["complete course", "learn course",
                                     "course on", "codechef", "coursera",
                                     "udemy", "do course"]):
            url_match = re.search(r'https?://\S+', goal)
            url = url_match.group() if url_match else ""
            return [
                self._make_step(1, "complete_course",
                    {"url": url},
                    "Opening and navigating the course"),
                self._make_step(2, "take_screenshot",
                    {},
                    "Capturing course state"),
            ]
            
        # ── JOB SEARCH ───────────────────────────────────────────
        if any(w in lower for w in ["find me", "jobs", "internship",
                                     "hiring", "vacancy", "career"]):
            city = "Chennai"
            for c in ["chennai","bangalore","mumbai","delhi",
                      "hyderabad","coimbatore","pune","remote"]:
                if c in lower: city = c.title(); break
            skill = "Python"
            for s in ["python","java","react","android","ml","ai",
                      "data","web","flutter","node","devops","c++"]:
                if s in lower: skill = s.title(); break
            return [
                self._make_step(1,"web_search",
                    {"query":f"{skill} jobs {city} 2026 fresher"},
                    f"Searching {skill} jobs in {city}"),
                self._make_step(2,"open_url",
                    {"url":f"https://www.linkedin.com/jobs/search/?keywords={skill}&location={city}"},
                    "Opening LinkedIn jobs"),
                self._make_step(3,"open_url",
                    {"url":f"https://www.naukri.com/{skill.lower()}-jobs-in-{city.lower()}"},
                    "Opening Naukri jobs"),
                self._make_step(4,"open_url",
                    {"url":f"https://internshala.com/internships/{skill.lower()}-internship-in-{city.lower()}"},
                    "Opening Internshala internships"),
            ]

        # ── RESEARCH ─────────────────────────────────────────────
        if any(w in lower for w in ["research","best","compare",
                                     "review","top","recommend"]):
            q = goal.replace(" ","+" )
            topic = re.sub(r'research|best|compare|review|top|'
                          r'recommend|under|above|find','',lower).strip()
            return [
                self._make_step(1,"web_search",
                    {"query": goal},
                    f"Searching: {goal}"),
                self._make_step(2,"open_url",
                    {"url":f"https://www.google.com/search?q={q}"},
                    "Opening Google results"),
                self._make_step(3,"youtube_search",
                    {"query": topic or goal},
                    f"Finding YouTube videos about {topic or goal}"),
            ]

        # ── STUDY / PLANNING ─────────────────────────────────────
        if any(w in lower for w in ["plan","schedule","organize",
                                     "study","timetable","routine"]):
            return [
                self._make_step(1,"get_reminders",{},
                    "Checking existing tasks and reminders"),
                self._make_step(2,"system_info",{},
                    "Checking system status"),
                self._make_step(3,"open_app",{"app":"notepad"},
                    "Opening Notepad for planning"),
            ]

        # ── SYSTEM HEALTH ─────────────────────────────────────────
        if any(w in lower for w in ["system health","optimize",
                                     "free memory","clean up","maintenance"]):
            return [
                self._make_step(1,"system_info",{},
                    "Checking CPU, RAM and disk"),
                self._make_step(2,"get_disk_usage",{},
                    "Checking disk space"),
                self._make_step(3,"empty_recycle_bin",{},
                    "Emptying recycle bin"),
                self._make_step(4,"list_processes",{},
                    "Listing heavy processes"),
            ]

        # ── YOUTUBE ───────────────────────────────────────────────
        if any(w in lower for w in ["youtube","tutorial","video",
                                     "watch","learn how"]):
            q = re.sub(r'search|youtube|find|watch|tutorial|video|'
                      r'learn how|on','',lower).strip()
            return [
                self._make_step(1,"youtube_search",
                    {"query": q or goal},
                    f"Searching YouTube: {q or goal}"),
                self._make_step(2,"open_url",
                    {"url":f"https://www.youtube.com/results?search_query={q.replace(' ','+')}"},
                    "Opening YouTube search results"),
            ]

        # ── NEWS / CURRENT EVENTS ─────────────────────────────────
        if any(w in lower for w in ["news","latest","current",
                                     "today","trending","what happened"]):
            topic = re.sub(r'news|latest|current|today|trending|'
                          r'what happened','',lower).strip()
            return [
                self._make_step(1,"web_search",
                    {"query":f"{topic} news today 2026"},
                    f"Searching latest news: {topic}"),
                self._make_step(2,"open_url",
                    {"url":f"https://news.google.com/search?q={topic.replace(' ','+')}"},
                    "Opening Google News"),
            ]

        # ── WEATHER + PLAN ────────────────────────────────────────
        if any(w in lower for w in ["weather","temperature","forecast"]):
            city = re.sub(r'weather|temperature|forecast|in|of|what|is',
                         '',lower).strip() or "Coimbatore"
            return [
                self._make_step(1,"get_weather",
                    {"city": city},
                    f"Getting weather for {city}"),
            ]
                # ── ONLINE COURSE ─────────────────────────────────────────
        if any(w in lower for w in ["complete course", "learn course",
                                     "finish course", "do course",
                                     "codechef", "coursera", "udemy",
                                     "course on"]):
            url = ""
            url_match = re.search(r'https?://\S+', goal)
            if url_match:
                url = url_match.group()
            return [
                self._make_step(1,"open_url",
                    {"url": url or "https://www.codechef.com/learn"},
                    "Opening the course page"),
                self._make_step(2,"take_screenshot",
                    {},
                    "Taking screenshot of course content"),
                self._make_step(3,"web_scrape",
                    {"url": url or "https://www.codechef.com/learn"},
                    "Reading course content"),
                self._make_step(4,"open_url",
                    {"url": url or "https://www.codechef.com/learn"},
                    "Navigating to first lesson"),
            ]
        # ── LLM FALLBACK ──────────────────────────────────────────
        try:
            from ollama import AsyncClient
            client = AsyncClient(host=self.config.ollama_base_url)
            prompt = f"""You are a task planner. Break this goal into 2-4 steps.

Goal: {goal}

Available tools (use EXACT names):
- web_search: {{"query": "search terms"}}
- open_url: {{"url": "https://..."}}
- youtube_search: {{"query": "search terms"}}
- get_reminders: {{}}
- system_info: {{}}
- open_app: {{"app": "chrome/notepad/spotify"}}
- get_weather: {{"city": "city name"}}
- translate_text: {{"text": "...", "target_lang": "ta/hi/fr"}}
- take_screenshot: {{}}
- get_disk_usage: {{}}

Return ONLY valid JSON array, nothing else:
[{{"step":1,"tool":"tool_name","args":{{"key":"value"}},"description":"short description"}}]"""

            resp = await client.chat(
                model="llama3.2:1b",
                messages=[{"role":"user","content":prompt}],
                stream=False,
                options={"temperature":0.1,"num_predict":400}
            )
            text = resp["message"]["content"].strip()
            # Extract JSON
            match = re.search(r'\[.*?\]', text, re.DOTALL)
            if match:
                steps = json.loads(match.group())
                if steps and isinstance(steps, list):
                    return steps
        except Exception as e:
            print(f"[Planner] LLM error: {e}")

        # ── LAST RESORT ───────────────────────────────────────────
        return [
            self._make_step(1,"web_search",
                {"query": goal},
                f"Searching: {goal}"),
            self._make_step(2,"open_url",
                {"url":f"https://www.google.com/search?q={goal.replace(' ','+')}"},
                "Opening Google results"),
        ]

# ── STEP EXECUTOR ─────────────────────────────────────────────────
class StepExecutor:
    def __init__(self, tools):
        self.tools = tools
        self.results = {}

    async def run(self, step: dict) -> dict:
        """Execute one step with retry."""
        tool = step.get("tool") or step.get("action", "")
        args = step.get("args", {})
        num  = step.get("step", 0)
        desc = step.get("description", tool)

        for attempt in range(2):
            try:
                result = await self.tools.execute(tool, args)
                self.results[num] = str(result)
                return {"step":num,"tool":tool,"description":desc,
                       "result":str(result),"success":True}
            except Exception as e:
                if attempt == 0:
                    await asyncio.sleep(1)
                else:
                    return {"step":num,"tool":tool,"description":desc,
                           "result":str(e),"success":False}

# ── REFLECTOR ─────────────────────────────────────────────────────
class Reflector:
    def __init__(self, config):
        self.config = config

    async def summarize(self, goal: str, results: list) -> str:
        """Generate summary of completed task."""
        done   = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]

        if not failed:
            return (f"All {len(done)} steps completed successfully, Sir. "
                   f"Goal achieved: {goal[:50]}.")
        return (f"Completed {len(done)} of {len(results)} steps, Sir. "
               f"{len(failed)} step(s) had issues but I did my best.")

    async def learn(self, goal: str, results: list, memory: AgenticMemory):
        """Save learned patterns."""
        tools = [r["tool"] for r in results if r.get("success")]
        if tools:
            key = f"goal_{goal[:20].replace(' ','_')}"
            memory.remember(key, {"goal":goal,"tools":tools,
                "success_rate": len([r for r in results
                                    if r.get("success")])/len(results)})

# ── AGENTIC TASK ──────────────────────────────────────────────────
class AgenticTask:
    def __init__(self, goal: str):
        self.id      = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.goal    = goal
        self.status  = PENDING
        self.steps   = []
        self.results = []
        self.summary = ""
        self.created = datetime.now().isoformat()

    def to_dict(self):
        done = len([r for r in self.results if r.get("success")])
        return {"id":self.id,"goal":self.goal,"status":self.status,
                "total_steps":len(self.steps),
                "completed_steps":done,
                "summary":self.summary,"created":self.created}

# ── MAIN AGENTIC MANAGER ──────────────────────────────────────────
class AgenticManager:
    def __init__(self, config, tools):
        self.config    = config
        self.tools     = tools
        self.planner   = SmartPlanner(config)
        self.executor  = StepExecutor(tools)
        self.reflector = Reflector(config)
        self.memory    = AgenticMemory()
        self.history   = []
        self.active    = None

    async def run_goal(self, goal: str, callback=None) -> str:
        """Full agentic task execution pipeline."""
        task = AgenticTask(goal)
        self.active = task
        self.history.append(task)

        try:
            # ── PHASE 1: ANNOUNCE ─────────────────────────────────
            task.status = PLANNING
            if callback:
                await callback({"type":"agentic_start",
                               "goal":goal,"task_id":task.id})
                await callback({"type":"token",
                               "content":f"🧠 Planning: {goal}\n\n"})

            # ── PHASE 2: PLAN ─────────────────────────────────────
            steps = await self.planner.plan(goal)
            task.steps = steps

            if not steps:
                task.status = FAILED
                if callback:
                    await callback({"type":"done"})
                return "I could not plan steps for that goal, Sir."

            task.status = RUNNING
            if callback:
                await callback({"type":"token",
                    "content":f"📋 {len(steps)} steps planned:\n"})
                for s in steps:
                    await callback({"type":"token",
                        "content":f"  {s['step']}. {s['description']}\n"})
                await callback({"type":"token","content":"\n"})

            # ── PHASE 3: EXECUTE ──────────────────────────────────
            executor = StepExecutor(self.tools)
            results  = []

            for step in steps:
                num  = step.get("step",0)
                desc = step.get("description","")

                if callback:
                    await callback({"type":"token",
                        "content":f"⚡ Step {num}: {desc}...\n"})

                result = await executor.run(step)
                results.append(result)

                status = "✅" if result["success"] else "❌"
                snippet = str(result.get("result",""))[:60]
                if callback:
                    await callback({"type":"token",
                        "content":f"{status} {snippet}\n"})

                await asyncio.sleep(0.3)

            task.results = results

            # ── PHASE 4: REFLECT ──────────────────────────────────
            if callback:
                await callback({"type":"token",
                    "content":"\n🔍 Summarizing results...\n"})

            summary = await self.reflector.summarize(goal, results)
            await self.reflector.learn(goal, results, self.memory)

            task.status  = DONE
            task.summary = summary

            self.memory.add({"goal":goal,
                "done":len([r for r in results if r.get("success")]),
                "total":len(results),
                "time":datetime.now().isoformat()})

            if callback:
                await callback({"type":"token",
                    "content":f"\n📊 {summary}\n"})
                await callback({"type":"done"})

            self._save()
            return summary

        except Exception as e:
            task.status = FAILED
            print(f"[Agentic] Fatal: {e}")
            if callback:
                await callback({"type":"done"})
            return f"Agentic task encountered an error, Sir: {str(e)[:80]}"
        finally:
            self.active = None

    def _save(self):
        try:
            TASKS_FILE.write_text(json.dumps(
                [t.to_dict() for t in self.history[-20:]], indent=2))
        except: pass

    def get_history(self, n=10) -> list:
        return [t.to_dict() for t in self.history[-n:]]

    def get_active(self):
        return self.active.to_dict() if self.active else None

    def get_memory_stats(self) -> dict:
        return {
            "memories": len(self.memory.long_term),
            "context":  len(self.memory.short_term),
            "tasks_done":   len([t for t in self.history if t.status==DONE]),
            "tasks_failed": len([t for t in self.history if t.status==FAILED]),
        }
    def is_agentic_goal(text: str) -> bool:
        lower = text.lower().strip()
        if any(e in lower for e in AGENTIC_EXCLUDE):
            return False
        has_trigger = any(t in lower for t in AGENTIC_TRIGGERS)
        return has_trigger and len(text.split()) > 2  # changed from 4 to 2

# ── GOAL DETECTOR ─────────────────────────────────────────────────
AGENTIC_TRIGGERS = [
    "find me", "research", "book a", "plan a",
    "help me plan", "i need you to", "organize",
    "create a plan", "set up", "do everything",
    "handle", "manage", "automatically",
    "complete task", "step by step", "can you do",
    "take care of", "look for jobs", "find jobs",
    "check system health", "system health",
    "complete course", "learn course", "course on",
    "codechef", "coursera", "udemy", "do course",
    "complete course", "learn course", "finish course",
    "do course", "course on", "codechef", "coursera",
    "find internship", "search and open",
    "find and open", "latest news", "current news",
]

AGENTIC_EXCLUDE = [
    "hi", "hello", "how are you", "what is",
    "who are you", "volume", "lock", "shutdown",
    "play song", "open chrome", "show", "mute",
    "brightness", "battery", "system info",
    "take screenshot", "weather in",
]

def is_agentic_goal(text: str) -> bool:
    """Detect if input needs agentic multi-step execution."""
    lower = text.lower().strip()
    if any(e in lower for e in AGENTIC_EXCLUDE):
        return False
    has_trigger = any(t in lower for t in AGENTIC_TRIGGERS)
    return has_trigger and len(text.split()) > 4