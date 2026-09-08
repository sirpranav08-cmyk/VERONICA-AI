"""
VERONICA - Complete Agentic AI Engine

Features:
- Goal decomposition
- Multi-step planning
- Ollama tool calling
- Tool execution
- Retry handling
- Failure recovery / replanning
- Self reflection
- Long-term memory
- Short-term context
- Persistent task history
- Tool schema generation
- Agentic goal detection

Requirements:
    pip install ollama

Your config object should provide:
    config.model
    config.agentic_model       # optional
    config.ollama_base_url     # e.g. http://127.0.0.1:11434

Your ToolRegistry should provide:
    tools.registry
    tools.execute(tool_name, args)
"""

import asyncio
import json
import re
from collections import deque
from datetime import datetime
from pathlib import Path
from uuid import uuid4


# ================================================================
# PATHS
# ================================================================

DATA_DIR = Path("D:/jarvis-agent/agent/data")
TASKS_FILE = DATA_DIR / "agentic_tasks.json"
MEMORY_FILE = DATA_DIR / "agentic_memory.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)


# ================================================================
# TASK STATES
# ================================================================

TASK_PENDING = "pending"
TASK_PLANNING = "planning"
TASK_RUNNING = "running"
TASK_DONE = "done"
TASK_FAILED = "failed"
TASK_RETRYING = "retrying"


# ================================================================
# TOOL SCHEMA
# ================================================================

def _infer_json_type(desc: str) -> str:
    """
    Best-effort conversion of ToolRegistry argument descriptions
    into JSON Schema types.
    """

    d = str(desc).lower().strip()

    # Boolean
    if any(word in d for word in [
        "bool",
        "boolean",
        "true or false"
    ]):
        return "boolean"

    # Integer
    if any(word in d for word in [
        "int ",
        "integer",
        "count",
        "amount",
        "level",
        "delay",
        "seconds",
        "minutes"
    ]):
        return "integer"

    # Number / float
    if any(word in d for word in [
        "float",
        "double",
        "decimal",
        "number"
    ]):
        return "number"

    # Default
    return "string"


def build_tool_schemas(tool_registry) -> list:
    """
    Convert ToolRegistry registry information into Ollama
    function-tool schemas.

    Expected registry format:

    registry = {
        "tool_name": {
            "description": "...",
            "args_schema": {
                "arg": "string description"
            }
        }
    }
    """

    schemas = []

    registry = getattr(tool_registry, "registry", {})

    if not isinstance(registry, dict):
        print("[Tool Schema] Invalid registry format.")
        return schemas

    for name, info in registry.items():

        if not isinstance(info, dict):
            continue

        properties = {}
        required = []

        args_schema = info.get("args_schema") or {}

        if isinstance(args_schema, dict):

            for arg_name, arg_desc in args_schema.items():

                properties[arg_name] = {
                    "type": _infer_json_type(arg_desc),
                    "description": str(arg_desc),
                }

                required.append(arg_name)

        schema = {
            "type": "function",
            "function": {
                "name": str(name),
                "description": str(
                    info.get("description", name)
                ),
                "parameters": {
                    "type": "object",
                    "properties": properties,
                },
            },
        }

        if required:
            schema["function"]["parameters"]["required"] = required

        schemas.append(schema)

    return schemas


# ================================================================
# AGENTIC MEMORY
# ================================================================

class AgenticMemory:

    def __init__(self):
        self.short_term = deque(maxlen=20)
        self.long_term = {}

        self.load()

    # ------------------------------------------------------------

    def load(self):
        """Load long-term memory from disk."""

        if not MEMORY_FILE.exists():
            return

        try:

            data = json.loads(
                MEMORY_FILE.read_text(
                    encoding="utf-8"
                )
            )

            if isinstance(data, dict):
                self.long_term = data.get(
                    "long_term",
                    {}
                )

        except Exception as e:
            print(
                f"[Memory] Failed to load memory: {e}"
            )

            self.long_term = {}

    # ------------------------------------------------------------

    def save(self):
        """Save memory to disk."""

        try:

            MEMORY_FILE.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            MEMORY_FILE.write_text(
                json.dumps(
                    {
                        "long_term": self.long_term
                    },
                    indent=2,
                    ensure_ascii=False
                ),
                encoding="utf-8"
            )

        except Exception as e:
            print(
                f"[Memory] Failed to save memory: {e}"
            )

    # ------------------------------------------------------------

    def remember(self, key: str, value):
        """Store information in long-term memory."""

        self.long_term[key] = {
            "value": value,
            "time": datetime.now().isoformat()
        }

        self.save()

    # ------------------------------------------------------------

    def recall(self, key: str):
        """Retrieve long-term memory."""

        return self.long_term.get(
            key,
            {}
        ).get("value")

    # ------------------------------------------------------------

    def add_context(self, item: dict):
        """Add information to short-term context."""

        self.short_term.append(item)

    # ------------------------------------------------------------

    def get_context(self) -> list:
        """Return short-term context."""

        return list(self.short_term)


# ================================================================
# GOAL PLANNER
# ================================================================

class GoalPlanner:

    def __init__(self, config, tool_schemas: list):

        self.config = config

        self.model = (
            getattr(config, "agentic_model", None)
            or getattr(config, "model", None)
        )

        self.ollama_base_url = getattr(
            config,
            "ollama_base_url",
            "http://127.0.0.1:11434"
        )

        self.tool_schemas = tool_schemas

    # ------------------------------------------------------------

    async def decompose(
        self,
        goal: str
    ) -> list:
        """
        Break a goal into executable steps.

        Uses deterministic patterns first and Ollama
        as the fallback planner.
        """

        lower = goal.lower().strip()

        # --------------------------------------------------------
        # JOB SEARCH
        # --------------------------------------------------------

        if any(
            word in lower
            for word in [
                "find me",
                "jobs",
                "internship",
                "work",
                "career",
                "hiring"
            ]
        ):

            location = "Chennai"

            cities = [
                "chennai",
                "bangalore",
                "bengaluru",
                "mumbai",
                "delhi",
                "hyderabad",
                "coimbatore",
                "pune"
            ]

            for city in cities:

                if city in lower:

                    if city == "bengaluru":
                        location = "Bangalore"
                    else:
                        location = city.title()

                    break

            skill = "Python"

            skills = [
                "python",
                "java",
                "react",
                "android",
                "ml",
                "ai",
                "data",
                "web",
                "flutter",
                "javascript",
                "c++"
            ]

            for skill_name in skills:

                if skill_name in lower:

                    skill = skill_name.title()

                    break

            return [
                {
                    "step": 1,
                    "tool": "web_search",
                    "args": {
                        "query": (
                            f"{skill} jobs in "
                            f"{location} 2026"
                        )
                    },
                    "description": (
                        f"Searching for {skill} "
                        f"jobs in {location}"
                    )
                },
                {
                    "step": 2,
                    "tool": "open_url",
                    "args": {
                        "url": (
                            "https://www.linkedin.com/jobs/"
                            f"search/?keywords={skill}"
                            f"&location={location}"
                        )
                    },
                    "description": "Opening LinkedIn jobs"
                },
                {
                    "step": 3,
                    "tool": "open_url",
                    "args": {
                        "url": (
                            "https://www.naukri.com/"
                            f"{skill.lower()}-jobs-in-"
                            f"{location.lower()}"
                        )
                    },
                    "description": "Opening Naukri jobs"
                }
            ]

        # --------------------------------------------------------
        # RESEARCH
        # --------------------------------------------------------

        if any(
            word in lower
            for word in [
                "research",
                "best",
                "compare",
                "review",
                "top"
            ]
        ):

            topic = re.sub(
                r"\b(research|best|compare|review|top|under|above)\b",
                "",
                lower,
                flags=re.IGNORECASE
            )

            topic = re.sub(
                r"\s+",
                " ",
                topic
            ).strip()

            return [
                {
                    "step": 1,
                    "tool": "web_search",
                    "args": {
                        "query": goal
                    },
                    "description": (
                        f"Searching: {goal}"
                    )
                },
                {
                    "step": 2,
                    "tool": "open_url",
                    "args": {
                        "url": (
                            "https://www.google.com/search?q="
                            + goal.replace(" ", "+")
                        )
                    },
                    "description": (
                        "Opening Google search results"
                    )
                },
                {
                    "step": 3,
                    "tool": "youtube_search",
                    "args": {
                        "query": topic or goal
                    },
                    "description": (
                        f"Finding YouTube videos about "
                        f"{topic or goal}"
                    )
                }
            ]

        # --------------------------------------------------------
        # SCHEDULE / PLANNING
        # --------------------------------------------------------

        if any(
            word in lower
            for word in [
                "plan",
                "schedule",
                "organize",
                "study plan",
                "week"
            ]
        ):

            return [
                {
                    "step": 1,
                    "tool": "get_reminders",
                    "args": {},
                    "description": (
                        "Checking existing tasks"
                    )
                },
                {
                    "step": 2,
                    "tool": "open_app",
                    "args": {
                        "app": "notepad"
                    },
                    "description": (
                        "Opening Notepad for planning"
                    )
                },
                {
                    "step": 3,
                    "tool": "system_info",
                    "args": {},
                    "description": (
                        "Checking system status"
                    )
                }
            ]

        # --------------------------------------------------------
        # SYSTEM HEALTH
        # --------------------------------------------------------

        if any(
            word in lower
            for word in [
                "system health",
                "optimize",
                "free memory",
                "clean"
            ]
        ):

            return [
                {
                    "step": 1,
                    "tool": "system_info",
                    "args": {},
                    "description": (
                        "Checking system health"
                    )
                },
                {
                    "step": 2,
                    "tool": "get_disk_usage",
                    "args": {},
                    "description": (
                        "Checking disk space"
                    )
                },
                {
                    "step": 3,
                    "tool": "empty_recycle_bin",
                    "args": {},
                    "description": (
                        "Emptying recycle bin"
                    )
                }
            ]

        # --------------------------------------------------------
        # YOUTUBE
        # --------------------------------------------------------

        if any(
            word in lower
            for word in [
                "youtube",
                "tutorial",
                "video",
                "watch"
            ]
        ):

            query = re.sub(
                r"\b(search|youtube|find|watch|tutorial|video)\b",
                "",
                lower,
                flags=re.IGNORECASE
            )

            query = re.sub(
                r"\s+",
                " ",
                query
            ).strip()

            return [
                {
                    "step": 1,
                    "tool": "youtube_search",
                    "args": {
                        "query": query or goal
                    },
                    "description": (
                        f"Searching YouTube for "
                        f"{query or goal}"
                    )
                }
            ]

        # --------------------------------------------------------
        # LLM PLANNING
        # --------------------------------------------------------

        return await self._llm_plan(goal)

    # ------------------------------------------------------------

    async def _llm_plan(
        self,
        goal: str
    ) -> list:
        """
        Use Ollama to generate a plan.

        Native tool calling is preferred.
        """

        try:

            from ollama import AsyncClient

        except ImportError:

            print(
                "[Planner] Ollama Python package "
                "is not installed."
            )

            return self._fallback_plan(goal)

        if not self.model:

            print(
                "[Planner] No Ollama model configured."
            )

            return self._fallback_plan(goal)

        try:

            client = AsyncClient(
                host=self.ollama_base_url
            )

            system = """
You are VERONICA's planning engine.

Break the user's goal into executable actions.

Use ONLY tools provided to you.

Call tools when appropriate.

If the task requires multiple actions, perform
the actions in logical order.

Do not invent tool names.
"""

            response = await client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system
                    },
                    {
                        "role": "user",
                        "content": goal
                    }
                ],
                tools=self.tool_schemas,
                stream=False,
                options={
                    "temperature": 0.1
                }
            )

            message = (
                response.get("message", {})
                or {}
            )

            tool_calls = (
                message.get("tool_calls")
                or []
            )

            steps = []

            for index, call in enumerate(
                tool_calls,
                start=1
            ):

                function = (
                    call.get("function", {})
                    or {}
                )

                name = function.get("name")

                if not name:
                    continue

                arguments = (
                    function.get("arguments")
                    or {}
                )

                if not isinstance(
                    arguments,
                    dict
                ):
                    arguments = {}

                steps.append(
                    {
                        "step": index,
                        "tool": name,
                        "args": arguments,
                        "description": (
                            f"Executing {name}"
                        ),
                        "depends_on": (
                            [index - 1]
                            if index > 1
                            else []
                        )
                    }
                )

            if steps:
                return steps

            # Some models return JSON text instead
            content = (
                message.get("content")
                or ""
            ).strip()

            parsed = self._extract_json_array(
                content
            )

            if parsed:
                return parsed

        except Exception as e:

            print(
                f"[Planner] LLM error: {e}"
            )

        return self._fallback_plan(goal)

    # ------------------------------------------------------------

    @staticmethod
    def _extract_json_array(
        text: str
    ) -> list:

        if not text:
            return []

        try:

            data = json.loads(text)

            if isinstance(data, list):
                return data

        except Exception:
            pass

        match = re.search(
            r"\[\s*\{.*\}\s*\]",
            text,
            re.DOTALL
        )

        if not match:
            return []

        try:

            data = json.loads(
                match.group(0)
            )

            return (
                data
                if isinstance(data, list)
                else []
            )

        except Exception:
            return []

    # ------------------------------------------------------------

    @staticmethod
    def _fallback_plan(
        goal: str
    ) -> list:

        return [
            {
                "step": 1,
                "tool": "web_search",
                "args": {
                    "query": goal
                },
                "description": (
                    f"Searching for: {goal}"
                )
            },
            {
                "step": 2,
                "tool": "open_url",
                "args": {
                    "url": (
                        "https://www.google.com/search?q="
                        + goal.replace(" ", "+")
                    )
                },
                "description": (
                    "Opening Google search results"
                )
            }
        ]

    # ------------------------------------------------------------

    async def replan(
        self,
        goal: str,
        failed_step: dict,
        error: str
    ) -> list:
        """
        Recover from a failed step using one
        Ollama tool call.
        """

        try:

            from ollama import AsyncClient

            client = AsyncClient(
                host=self.ollama_base_url
            )

            system = """
You are VERONICA's recovery planner.

A tool execution failed.

Select exactly ONE available tool that can
best recover from the failure.

Do not call unavailable tools.
"""

            user = (
                f"Goal: {goal}\n\n"
                f"Failed step:\n"
                f"{json.dumps(failed_step, indent=2)}\n\n"
                f"Error:\n{error}\n\n"
                "Recover from this failure."
            )

            response = await client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system
                    },
                    {
                        "role": "user",
                        "content": user
                    }
                ],
                tools=self.tool_schemas,
                stream=False,
                options={
                    "temperature": 0.2
                }
            )

            message = (
                response.get("message", {})
                or {}
            )

            tool_calls = (
                message.get("tool_calls")
                or []
            )

            if not tool_calls:
                return []

            function = (
                tool_calls[0].get(
                    "function",
                    {}
                )
                or {}
            )

            name = function.get("name")

            if not name:
                return []

            arguments = (
                function.get("arguments")
                or {}
            )

            if not isinstance(
                arguments,
                dict
            ):
                arguments = {}

            return [
                {
                    "step": failed_step.get(
                        "step",
                        99
                    ),
                    "tool": name,
                    "args": arguments,
                    "description": (
                        f"Recovery: call {name}"
                    ),
                    "depends_on": []
                }
            ]

        except Exception as e:

            print(
                f"[Planner] Replan error: {e}"
            )

            return []


# ================================================================
# STEP EXECUTOR
# ================================================================

class StepExecutor:

    def __init__(
        self,
        tools,
        max_retries: int = 3
    ):

        self.tools = tools
        self.max_retries = max(
            1,
            max_retries
        )

        self.results = {}

    # ------------------------------------------------------------

    async def execute(
        self,
        step: dict
    ) -> dict:

        tool = (
            step.get("tool")
            or step.get("action")
        )

        args = step.get(
            "args",
            {}
        )

        step_num = step.get(
            "step",
            0
        )

        description = step.get(
            "description",
            str(tool)
        )

        if not tool:

            return {
                "step": step_num,
                "tool": None,
                "description": description,
                "result": (
                    "No tool specified."
                ),
                "success": False,
                "attempts": 0
            }

        print(
            f"[Executor] Step {step_num}: "
            f"{description}"
        )

        last_error = ""

        for attempt in range(
            1,
            self.max_retries + 1
        ):

            try:

                result = await self.tools.execute(
                    tool,
                    args
                )

                self.results[
                    step_num
                ] = result

                return {
                    "step": step_num,
                    "tool": tool,
                    "description": description,
                    "result": result,
                    "success": True,
                    "attempts": attempt
                }

            except Exception as e:

                last_error = str(e)

                print(
                    f"[Executor] "
                    f"Attempt {attempt}/"
                    f"{self.max_retries} failed: "
                    f"{e}"
                )

                if attempt < self.max_retries:

                    await asyncio.sleep(
                        min(
                            attempt,
                            3
                        )
                    )

        return {
            "step": step_num,
            "tool": tool,
            "description": description,
            "result": last_error,
            "success": False,
            "attempts": self.max_retries
        }

    # ------------------------------------------------------------

    def get_result(
        self,
        step_num: int
    ):

        return self.results.get(
            step_num,
            ""
        )


# ================================================================
# REFLECTOR
# ================================================================

class Reflector:

    def __init__(
        self,
        config
    ):

        self.config = config

        self.model = (
            getattr(
                config,
                "agentic_model",
                None
            )
            or getattr(
                config,
                "model",
                None
            )
        )

        self.ollama_base_url = getattr(
            config,
            "ollama_base_url",
            "http://127.0.0.1:11434"
        )

    # ------------------------------------------------------------

    async def reflect(
        self,
        goal: str,
        steps: list,
        results: list
    ) -> str:

        completed = [
            r for r in results
            if r.get("success")
        ]

        failed = [
            r for r in results
            if not r.get("success")
        ]

        if not self.model:

            return self._basic_summary(
                completed,
                failed
            )

        try:

            from ollama import AsyncClient

            client = AsyncClient(
                host=self.ollama_base_url
            )

            result_summary = []

            for result in results:

                result_summary.append(
                    {
                        "step": result.get(
                            "step"
                        ),
                        "action": result.get(
                            "description"
                        ),
                        "success": result.get(
                            "success"
                        )
                    }
                )

            prompt = f"""
Goal:
{goal}

Completed:
{len(completed)}/{len(results)}

Results:
{json.dumps(result_summary, indent=2)}

Write a concise two-sentence summary
addressing the user as Sir.

Be honest about what succeeded and failed.
"""

            response = await client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                stream=False,
                options={
                    "temperature": 0.3,
                    "num_predict": 120
                }
            )

            message = (
                response.get("message", {})
                or {}
            )

            content = (
                message.get("content")
                or ""
            ).strip()

            if content:
                return content

        except Exception as e:

            print(
                f"[Reflector] Error: {e}"
            )

        return self._basic_summary(
            completed,
            failed
        )

    # ------------------------------------------------------------

    @staticmethod
    def _basic_summary(
        completed,
        failed
    ) -> str:

        if failed:

            return (
                f"Completed {len(completed)} "
                f"step(s), Sir. "
                f"{len(failed)} step(s) "
                f"encountered issues."
            )

        return (
            f"All {len(completed)} "
            f"step(s) completed successfully, Sir."
        )

    # ------------------------------------------------------------

    async def learn(
        self,
        goal: str,
        results: list,
        memory: AgenticMemory
    ):

        if not results:
            return

        successful_tools = [
            r.get("tool")
            for r in results
            if r.get("success")
        ]

        success_count = len(
            successful_tools
        )

        success_rate = (
            success_count / len(results)
        )

        if successful_tools:

            safe_goal = re.sub(
                r"[^a-zA-Z0-9_-]",
                "_",
                goal[:40]
            )

            pattern_key = (
                f"pattern_{safe_goal}"
            )

            memory.remember(
                pattern_key,
                {
                    "goal": goal,
                    "tools": successful_tools,
                    "success_rate": success_rate
                }
            )


# ================================================================
# TASK
# ================================================================

class AgenticTask:

    def __init__(
        self,
        goal: str,
        task_id: str = None
    ):

        timestamp = datetime.now()

        self.id = (
            task_id
            or
            f"{timestamp:%Y%m%d_%H%M%S}_"
            f"{uuid4().hex[:6]}"
        )

        self.goal = goal

        self.status = TASK_PENDING

        self.steps = []

        self.results = []

        self.created = (
            timestamp.isoformat()
        )

        self.completed = None

        self.summary = ""

    # ------------------------------------------------------------

    def to_dict(self) -> dict:

        return {
            "id": self.id,
            "goal": self.goal,
            "status": self.status,
            "steps": len(self.steps),
            "completed_steps": len([
                r for r in self.results
                if r.get("success")
            ]),
            "created": self.created,
            "completed": self.completed,
            "summary": self.summary
        }


# ================================================================
# MAIN AGENTIC MANAGER
# ================================================================

class AgenticManager:

    def __init__(
        self,
        config,
        tools
    ):

        self.config = config

        self.tools = tools

        self.tool_schemas = (
            build_tool_schemas(tools)
        )

        self.planner = GoalPlanner(
            config,
            self.tool_schemas
        )

        self.executor = StepExecutor(
            tools
        )

        self.reflector = Reflector(
            config
        )

        self.memory = AgenticMemory()

        self.task_queue = asyncio.Queue()

        self.task_history = []

        self.active_task = None

        self._load_history()

    # ------------------------------------------------------------

    def _load_history(self):

        if not TASKS_FILE.exists():
            return

        try:

            data = json.loads(
                TASKS_FILE.read_text(
                    encoding="utf-8"
                )
            )

            if not isinstance(
                data,
                list
            ):
                return

            for item in data:

                if not isinstance(
                    item,
                    dict
                ):
                    continue

                task = AgenticTask(
                    goal=item.get(
                        "goal",
                        ""
                    ),
                    task_id=item.get(
                        "id"
                    )
                )

                task.status = item.get(
                    "status",
                    TASK_PENDING
                )

                task.created = item.get(
                    "created",
                    task.created
                )

                task.completed = item.get(
                    "completed"
                )

                task.summary = item.get(
                    "summary",
                    ""
                )

                self.task_history.append(
                    task
                )

        except Exception as e:

            print(
                f"[Agentic] Failed to load "
                f"task history: {e}"
            )

    # ------------------------------------------------------------

    def refresh_tool_schemas(self):

        self.tool_schemas = (
            build_tool_schemas(
                self.tools
            )
        )

        self.planner.tool_schemas = (
            self.tool_schemas
        )

        print(
            f"[Agentic] Loaded "
            f"{len(self.tool_schemas)} tools."
        )

    # ------------------------------------------------------------

    async def run_goal(
        self,
        goal: str,
        callback=None
    ) -> str:

        if not goal or not goal.strip():

            return (
                "Please provide a goal, Sir."
            )

        goal = goal.strip()

        task = AgenticTask(
            goal
        )

        self.active_task = task

        self.task_history.append(
            task
        )

        try:

            # ====================================================
            # PHASE 1 — PLANNING
            # ====================================================

            task.status = TASK_PLANNING

            await self._callback(
                callback,
                {
                    "type": "agentic_start",
                    "goal": goal,
                    "task_id": task.id
                }
            )

            await self._callback(
                callback,
                {
                    "type": "token",
                    "content": (
                        f"🧠 Planning how to: "
                        f"{goal}\n"
                    )
                }
            )

            steps = await self.planner.decompose(
                goal
            )

            if not steps:

                task.status = TASK_FAILED

                message = (
                    "I could not plan any tool "
                    "calls for that goal, Sir."
                )

                await self._callback(
                    callback,
                    {
                        "type": "token",
                        "content": message
                    }
                )

                return message

            task.steps = steps

            task.status = TASK_RUNNING

            await self._callback(
                callback,
                {
                    "type": "token",
                    "content": (
                        f"📋 {len(steps)} steps "
                        f"planned. Executing...\n\n"
                    )
                }
            )

            # ====================================================
            # PHASE 2 — EXECUTION
            # ====================================================

            executor = StepExecutor(
                self.tools,
                max_retries=3
            )

            results = []

            for step in steps:

                step_num = step.get(
                    "step",
                    0
                )

                description = step.get(
                    "description",
                    ""
                )

                await self._callback(
                    callback,
                    {
                        "type": "token",
                        "content": (
                            f"⚡ Step {step_num}: "
                            f"{description}\n"
                        )
                    }
                )

                result = await executor.execute(
                    step
                )

                results.append(
                    result
                )

                status_icon = (
                    "✅"
                    if result["success"]
                    else "❌"
                )

                result_text = str(
                    result.get(
                        "result",
                        ""
                    )
                )

                await self._callback(
                    callback,
                    {
                        "type": "token",
                        "content": (
                            f"{status_icon} "
                            f"{result_text[:150]}\n"
                        )
                    }
                )

                # =================================================
                # RECOVERY
                # =================================================

                if not result["success"]:

                    task.status = (
                        TASK_RETRYING
                    )

                    await self._callback(
                        callback,
                        {
                            "type": "token",
                            "content": (
                                "🔄 Step failed. "
                                "Attempting recovery...\n"
                            )
                        }
                    )

                    recovery = (
                        await self.planner.replan(
                            goal,
                            step,
                            result["result"]
                        )
                    )

                    if recovery:

                        recovery_step = (
                            recovery[0]
                        )

                        await self._callback(
                            callback,
                            {
                                "type": "token",
                                "content": (
                                    "🛠️ Recovery action: "
                                    f"{recovery_step.get('tool')}\n"
                                )
                            }
                        )

                        recovery_result = (
                            await executor.execute(
                                recovery_step
                            )
                        )

                        results.append(
                            recovery_result
                        )

                        recovery_icon = (
                            "✅"
                            if recovery_result[
                                "success"
                            ]
                            else "❌"
                        )

                        await self._callback(
                            callback,
                            {
                                "type": "token",
                                "content": (
                                    f"{recovery_icon} "
                                    f"Recovery completed.\n"
                                )
                            }
                        )

                    task.status = TASK_RUNNING

                await asyncio.sleep(
                    0.2
                )

            task.results = results

            # ====================================================
            # PHASE 3 — REFLECTION
            # ====================================================

            await self._callback(
                callback,
                {
                    "type": "token",
                    "content": (
                        "\n🔍 Reflecting on results...\n"
                    )
                }
            )

            summary = await self.reflector.reflect(
                goal,
                steps,
                results
            )

            await self.reflector.learn(
                goal,
                results,
                self.memory
            )

            successful = len([
                r for r in results
                if r.get("success")
            ])

            failed = len([
                r for r in results
                if not r.get("success")
            ])

            # ----------------------------------------------------
            # FINAL STATUS
            # ----------------------------------------------------

            if failed and successful == 0:

                task.status = TASK_FAILED

            else:

                task.status = TASK_DONE

            task.completed = (
                datetime.now().isoformat()
            )

            task.summary = summary

            self.memory.add_context(
                {
                    "goal": goal,
                    "success": successful,
                    "failed": failed,
                    "total": len(results),
                    "time": task.completed
                }
            )

            await self._callback(
                callback,
                {
                    "type": "done",
                    "summary": summary
                }
            )

            return summary

        except Exception as e:

            task.status = TASK_FAILED

            error_message = str(e)

            print(
                f"[Agentic] Fatal error: "
                f"{error_message}"
            )

            await self._callback(
                callback,
                {
                    "type": "token",
                    "content": (
                        f"\n❌ Agentic task failed: "
                        f"{error_message[:200]}\n"
                    )
                }
            )

            await self._callback(
                callback,
                {
                    "type": "done"
                }
            )

            return (
                f"Agentic task failed, Sir: "
                f"{error_message[:200]}"
            )

        finally:

            self.active_task = None

            self._save_history()

    # ------------------------------------------------------------

    @staticmethod
    async def _callback(
        callback,
        payload
    ):

        if callback is None:
            return

        try:

            result = callback(
                payload
            )

            if asyncio.iscoroutine(result):

                await result

        except Exception as e:

            print(
                f"[Callback] Error: {e}"
            )

    # ------------------------------------------------------------

    def _save_history(self):

        try:

            TASKS_FILE.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            data = [
                task.to_dict()
                for task in self.task_history[-20:]
            ]

            TASKS_FILE.write_text(
                json.dumps(
                    data,
                    indent=2,
                    ensure_ascii=False
                ),
                encoding="utf-8"
            )

        except Exception as e:

            print(
                f"[Agentic] Failed to save "
                f"history: {e}"
            )

    # ------------------------------------------------------------

    def get_history(self) -> list:

        return [
            task.to_dict()
            for task in self.task_history[-10:]
        ]

    # ------------------------------------------------------------

    def get_active_task(self):

        if self.active_task:

            return self.active_task.to_dict()

        return None

    # ------------------------------------------------------------

    def get_memory_stats(self) -> dict:

        return {
            "long_term_memories": (
                len(self.memory.long_term)
            ),
            "short_term_context": (
                len(
                    self.memory.get_context()
                )
            ),
            "tasks_completed": len([
                task
                for task in self.task_history
                if task.status == TASK_DONE
            ]),
            "tasks_failed": len([
                task
                for task in self.task_history
                if task.status == TASK_FAILED
            ]),
            "tools_available": len(
                self.tool_schemas
            )
        }


# ================================================================
# GOAL DETECTOR
# ================================================================

AGENTIC_TRIGGERS = [
    "find me",
    "research",
    "book a",
    "plan a",
    "help me plan",
    "i need you to",
    "organize",
    "create a plan",
    "set up",
    "do everything",
    "handle",
    "manage",
    "automatically",
    "complete task",
    "full task",
    "step by step",
    "can you do",
    "take care of",
    "look for",
    "search and open",
    "find and open",
]


AGENTIC_EXCLUDE = [
    "hi",
    "hello",
    "how are you",
    "what is",
    "who are you",
    "volume",
    "lock",
    "shutdown",
    "play",
    "open",
    "show",
    "mute",
    "brightness",
]


def is_agentic_goal(
    text: str
) -> bool:

    if not text:
        return False

    lower = text.lower().strip()

    # ------------------------------------------------------------
    # Exclusions
    # ------------------------------------------------------------

    if any(
        lower == item
        or lower.startswith(item + " ")
        for item in AGENTIC_EXCLUDE
    ):
        return False

    # ------------------------------------------------------------
    # Trigger detection
    # ------------------------------------------------------------

    has_trigger = any(
        trigger in lower
        for trigger in AGENTIC_TRIGGERS
    )

    word_count = len(
        text.split()
    )

    return (
        has_trigger
        and word_count > 4
    )


# ================================================================
# OPTIONAL DEBUG INFORMATION
# ================================================================

def get_agentic_status(
    manager: AgenticManager
) -> dict:

    return {
        "active_task": (
            manager.get_active_task()
        ),
        "history_count": len(
            manager.task_history
        ),
        "memory": (
            manager.get_memory_stats()
        ),
        "tools": len(
            manager.tool_schemas
        ),
        "planner_model": (
            manager.planner.model
        )
    }