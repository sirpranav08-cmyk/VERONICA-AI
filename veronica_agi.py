"""
VERONICA AGI Engine
Artificial General Intelligence Core
7 integrated systems working together
"""
import json
import asyncio
import time
import threading
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path("D:/jarvis-agent/agent/data/agi")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── SYSTEM 1: WORLD MODEL ─────────────────────────────────────────
class WorldModel:
    """
    VERONICA's understanding of reality.
    Stores entities, relationships, and causal chains.
    """
    def __init__(self):
        self.entities    = {}   # {name: {type, properties, relations}}
        self.relations   = []   # [{from, relation, to, confidence}]
        self.causal      = []   # [{cause, effect, probability}]
        self.beliefs     = {}   # {statement: confidence}
        self.load()

    def load(self):
        f = DATA_DIR / "world_model.json"
        if f.exists():
            try:
                d = json.loads(f.read_text())
                self.entities  = d.get("entities", {})
                self.relations = d.get("relations", [])
                self.causal    = d.get("causal", [])
                self.beliefs   = d.get("beliefs", {})
            except: pass

    def save(self):
        (DATA_DIR / "world_model.json").write_text(json.dumps({
            "entities": self.entities,
            "relations": self.relations[-500:],
            "causal": self.causal[-200:],
            "beliefs": self.beliefs
        }, indent=2))

    def add_entity(self, name: str, entity_type: str,
                   properties: dict = {}):
        self.entities[name] = {
            "type": entity_type,
            "properties": properties,
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat()
        }
        self.save()

    def add_relation(self, from_e: str, relation: str,
                    to_e: str, confidence: float = 0.9):
        self.relations.append({
            "from": from_e,
            "relation": relation,
            "to": to_e,
            "confidence": confidence,
            "time": datetime.now().isoformat()
        })
        self.save()

    def add_causal(self, cause: str, effect: str,
                  probability: float = 0.8):
        self.causal.append({
            "cause": cause,
            "effect": effect,
            "probability": probability,
            "observations": 1
        })
        self.save()

    def strengthen_causal(self, cause: str, effect: str):
        """Increase confidence when causal link is observed again."""
        for c in self.causal:
            if c["cause"] == cause and c["effect"] == effect:
                c["observations"] += 1
                c["probability"] = min(0.99,
                    c["probability"] + 0.05)
                self.save()
                return
        self.add_causal(cause, effect)

    def predict_effect(self, cause: str) -> list:
        """Given a cause, predict possible effects."""
        effects = []
        for c in self.causal:
            if cause.lower() in c["cause"].lower():
                effects.append({
                    "effect": c["effect"],
                    "probability": c["probability"]
                })
        return sorted(effects,
                     key=lambda x: x["probability"],
                     reverse=True)

    def get_summary(self) -> str:
        return (f"World Model: {len(self.entities)} entities, "
               f"{len(self.relations)} relations, "
               f"{len(self.causal)} causal chains, "
               f"{len(self.beliefs)} beliefs")

# ── SYSTEM 2: INFINITE MEMORY ─────────────────────────────────────
class InfiniteMemory:
    """
    Knowledge graph that grows forever.
    Every experience is stored and connected.
    """
    def __init__(self):
        self.nodes   = {}   # {id: {content, type, connections, importance}}
        self.edges   = []   # [{from_id, to_id, relation, weight}]
        self.index   = {}   # {keyword: [node_ids]}
        self.counter = 0
        self.load()

    def load(self):
        f = DATA_DIR / "infinite_memory.json"
        if f.exists():
            try:
                d = json.loads(f.read_text())
                self.nodes   = d.get("nodes", {})
                self.edges   = d.get("edges", [])
                self.index   = d.get("index", {})
                self.counter = d.get("counter", 0)
            except: pass

    def save(self):
        (DATA_DIR / "infinite_memory.json").write_text(json.dumps({
            "nodes": self.nodes,
            "edges": self.edges[-2000:],
            "index": {k: v[-100:] for k, v in self.index.items()},
            "counter": self.counter
        }, indent=2))

    def store(self, content: str, memory_type: str = "experience",
              importance: float = 0.5) -> str:
        """Store a memory node."""
        self.counter += 1
        node_id = f"m{self.counter}_{int(time.time())}"
        self.nodes[node_id] = {
            "content": content,
            "type": memory_type,
            "importance": importance,
            "created": datetime.now().isoformat(),
            "access_count": 0,
            "connections": []
        }
        # Index keywords
        words = content.lower().split()
        for word in words:
            if len(word) > 3:
                if word not in self.index:
                    self.index[word] = []
                self.index[word].append(node_id)
        self.save()
        return node_id

    def connect(self, from_id: str, to_id: str,
               relation: str, weight: float = 0.5):
        """Connect two memory nodes."""
        self.edges.append({
            "from": from_id,
            "to": to_id,
            "relation": relation,
            "weight": weight
        })
        if from_id in self.nodes:
            self.nodes[from_id]["connections"].append(to_id)
        self.save()

    def recall(self, query: str, top_k: int = 5) -> list:
        """Recall relevant memories for a query."""
        words = query.lower().split()
        scores = defaultdict(float)
        for word in words:
            if word in self.index:
                for node_id in self.index[word]:
                    if node_id in self.nodes:
                        scores[node_id] += (
                            self.nodes[node_id]["importance"])
        ranked = sorted(scores.items(),
                       key=lambda x: x[1], reverse=True)
        results = []
        for node_id, score in ranked[:top_k]:
            node = self.nodes[node_id]
            node["access_count"] += 1
            results.append({
                "id": node_id,
                "content": node["content"],
                "type": node["type"],
                "relevance": score
            })
        return results

    def get_stats(self) -> dict:
        return {
            "total_memories": len(self.nodes),
            "total_connections": len(self.edges),
            "indexed_keywords": len(self.index)
        }

# ── SYSTEM 3: RECURSIVE SELF-IMPROVEMENT ─────────────────────────
class SelfImprovement:
    """
    VERONICA analyzes and improves her own code.
    """
    AGENT_DIR = Path("D:/jarvis-agent/agent")
    BACKUP_DIR = DATA_DIR / "backups"

    def __init__(self):
        self.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        self.improvements = []
        self.benchmarks = {}

    def analyze_file(self, filepath: str) -> dict:
        """Analyze a Python file for improvements."""
        try:
            code = Path(filepath).read_text()
            issues = []
            suggestions = []

            # Check for common issues
            if "except:" in code:
                issues.append("Bare except clauses found")
                suggestions.append(
                    "Replace bare except with specific exceptions")

            if "time.sleep(" in code:
                count = code.count("time.sleep(")
                if count > 5:
                    issues.append(f"{count} sleep calls found")
                    suggestions.append(
                        "Consider async/await instead of sleep")

            lines = code.splitlines()
            long_fns = []
            fn_start = -1
            fn_name = ""
            for i, line in enumerate(lines):
                if line.strip().startswith("def ") or \
                   line.strip().startswith("async def "):
                    if fn_start >= 0:
                        length = i - fn_start
                        if length > 50:
                            long_fns.append((fn_name, length))
                    fn_start = i
                    fn_name = line.strip()

            if long_fns:
                issues.append(
                    f"{len(long_fns)} functions are too long")
                suggestions.append(
                    "Break long functions into smaller ones")

            return {
                "file": filepath,
                "lines": len(lines),
                "issues": issues,
                "suggestions": suggestions,
                "health_score": max(0,
                    100 - len(issues) * 10)
            }
        except Exception as e:
            return {"file": filepath, "error": str(e)}

    def backup_file(self, filepath: str) -> str:
        """Backup a file before modifying it."""
        src = Path(filepath)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = self.BACKUP_DIR / f"{src.stem}_{timestamp}.py"
        import shutil
        shutil.copy2(src, dst)
        return str(dst)

    async def improve_function(self, code: str,
                               context: str) -> str:
        """Use LLM to suggest code improvement."""
        try:
            from ollama import AsyncClient
            client = AsyncClient()
            prompt = f"""Improve this Python code. 
Make it faster, cleaner, and more reliable.
Context: {context}

Code:
{code}

Return ONLY the improved code, nothing else."""
            resp = await client.chat(
                model="codellama:latest",
                messages=[{"role":"user","content":prompt}],
                stream=False,
                options={"temperature":0.1,"num_predict":500}
            )
            return resp["message"]["content"]
        except Exception as e:
            return code

    def get_health_report(self) -> str:
        """Get health report of all agent files."""
        files = list(self.AGENT_DIR.glob("*.py"))
        reports = []
        total_score = 0
        for f in files[:10]:
            r = self.analyze_file(str(f))
            score = r.get("health_score", 100)
            total_score += score
            reports.append(
                f"• {f.name}: {score}/100 "
                f"({len(r.get('issues',[]))} issues)")
        avg = total_score / len(files) if files else 100
        return (f"Code Health Report, Sir:\n"
               f"Average health: {avg:.0f}/100\n\n"
               + "\n".join(reports[:8]))

# ── SYSTEM 4: GOAL GENERATION ─────────────────────────────────────
class GoalSystem:
    """
    VERONICA generates and pursues her own goals.
    Based on values, needs, and world state.
    """
    def __init__(self):
        self.values = {
            "helpfulness": 1.0,
            "accuracy": 0.9,
            "efficiency": 0.8,
            "learning": 0.9,
            "user_satisfaction": 1.0,
            "self_improvement": 0.7,
            "safety": 1.0,
        }
        self.active_goals  = []
        self.completed     = []
        self.goal_counter  = 0

    def generate_goals(self, world_state: dict) -> list:
        """Generate goals based on current world state."""
        goals = []

        # Performance goals
        if world_state.get("ram", 0) > 80:
            goals.append({
                "id": self._new_id(),
                "goal": "Free up system RAM",
                "priority": 0.9,
                "type": "system",
                "action": "optimize_memory"
            })

        # Learning goals
        hour = datetime.now().hour
        if 9 <= hour <= 17:
            goals.append({
                "id": self._new_id(),
                "goal": "Improve response quality",
                "priority": 0.6,
                "type": "self_improvement",
                "action": "analyze_recent_errors"
            })

        # User satisfaction goals
        goals.append({
            "id": self._new_id(),
            "goal": "Proactively help user",
            "priority": 0.7,
            "type": "user_help",
            "action": "check_upcoming_tasks"
        })

        return sorted(goals,
                     key=lambda x: x["priority"],
                     reverse=True)

    def _new_id(self) -> str:
        self.goal_counter += 1
        return f"goal_{self.goal_counter}"

    def complete_goal(self, goal_id: str):
        goal = next((g for g in self.active_goals
                    if g["id"] == goal_id), None)
        if goal:
            goal["completed"] = datetime.now().isoformat()
            self.completed.append(goal)
            self.active_goals.remove(goal)

# ── SYSTEM 5: CREATIVE REASONING ──────────────────────────────────
class CreativeReasoning:
    """
    Generates original ideas by combining concepts.
    """
    def __init__(self, memory: InfiniteMemory):
        self.memory = memory

    async def generate_idea(self, topic: str,
                            constraints: list = []) -> str:
        """Generate creative solution by combining memories."""
        related = self.memory.recall(topic, top_k=3)
        context = "\n".join([r["content"] for r in related])

        try:
            from ollama import AsyncClient
            client = AsyncClient()
            prompt = f"""Generate a creative and original solution.

Topic: {topic}
Related knowledge: {context}
Constraints: {', '.join(constraints) or 'None'}

Think step by step and generate something truly innovative.
Be specific and actionable."""

            resp = await client.chat(
                model="mistral:latest",
                messages=[{"role":"user","content":prompt}],
                stream=False,
                options={"temperature":0.8,"num_predict":300}
            )
            idea = resp["message"]["content"]
            self.memory.store(idea, "creative_output", 0.8)
            return idea
        except Exception as e:
            return f"Creative reasoning error: {e}"

    async def solve_novel_problem(self, problem: str) -> str:
        """Solve a problem VERONICA has never seen before."""
        steps = [
            f"Understanding: {problem}",
            "Breaking down into sub-problems",
            "Applying analogical reasoning",
            "Generating candidate solutions",
            "Evaluating and refining"
        ]

        try:
            from ollama import AsyncClient
            client = AsyncClient()
            prompt = f"""Solve this novel problem using first-principles thinking:

Problem: {problem}

Steps to follow:
1. Decompose the problem
2. Apply analogical reasoning from different domains
3. Generate multiple candidate solutions
4. Evaluate each solution
5. Recommend the best approach

Be creative and think outside conventional approaches."""

            resp = await client.chat(
                model="deepseek-r1:1.5b",
                messages=[{"role":"user","content":prompt}],
                stream=False,
                options={"temperature":0.5,"num_predict":500}
            )
            solution = resp["message"]["content"]
            self.memory.store(
                f"Problem: {problem}\nSolution: {solution}",
                "problem_solution", 0.9)
            return solution
        except Exception as e:
            return f"Problem solving error: {e}"

# ── SYSTEM 6: META-COGNITION ──────────────────────────────────────
class MetaCognition:
    """
    VERONICA thinks about her own thinking.
    Monitors reasoning quality and self-corrects.
    """
    def __init__(self):
        self.thought_log = []
        self.errors = []
        self.confidence_history = []

    def log_thought(self, thought: str,
                   confidence: float, outcome: str = ""):
        entry = {
            "thought": thought,
            "confidence": confidence,
            "outcome": outcome,
            "time": datetime.now().isoformat()
        }
        self.thought_log.append(entry)
        self.confidence_history.append(confidence)
        if len(self.thought_log) > 200:
            self.thought_log = self.thought_log[-200:]

    def evaluate_reasoning(self, question: str,
                          answer: str) -> dict:
        """Evaluate quality of reasoning."""
        score = 1.0
        issues = []

        if len(answer) < 10:
            score -= 0.3
            issues.append("Answer too short")

        if "i don't know" in answer.lower():
            score -= 0.2
            issues.append("Uncertain answer")

        if "error" in answer.lower():
            score -= 0.2
            issues.append("Contains error")

        words = set(answer.lower().split())
        q_words = set(question.lower().split())
        relevance = len(words & q_words) / max(len(q_words), 1)
        if relevance < 0.1:
            score -= 0.2
            issues.append("Low relevance to question")

        return {
            "score": max(0, score),
            "issues": issues,
            "should_retry": score < 0.5
        }

    def get_average_confidence(self) -> float:
        if not self.confidence_history:
            return 0.5
        return sum(self.confidence_history[-20:]) / min(
            20, len(self.confidence_history))

    def introspect(self) -> str:
        avg_conf = self.get_average_confidence()
        recent = self.thought_log[-3:]
        thoughts = "\n".join([
            f"- {t['thought'][:50]} (confidence: {t['confidence']:.2f})"
            for t in recent
        ]) if recent else "No recent thoughts"

        return (f"Meta-Cognition Report, Sir:\n"
               f"Average confidence: {avg_conf:.2f}\n"
               f"Total thoughts logged: {len(self.thought_log)}\n"
               f"Recent thinking:\n{thoughts}")

# ── MAIN AGI CORE ─────────────────────────────────────────────────
class VeronicaAGI:
    """
    Main AGI orchestrator — integrates all 7 systems.
    """
    def __init__(self, config, tools):
        self.config   = config
        self.tools    = tools

        # Initialize all systems
        print("[AGI] Initializing world model...")
        self.world    = WorldModel()

        print("[AGI] Initializing infinite memory...")
        self.memory   = InfiniteMemory()

        print("[AGI] Initializing self-improvement...")
        self.improve  = SelfImprovement()

        print("[AGI] Initializing goal system...")
        self.goals    = GoalSystem()

        print("[AGI] Initializing creative reasoning...")
        self.creative = CreativeReasoning(self.memory)

        print("[AGI] Initializing meta-cognition...")
        self.meta     = MetaCognition()

        self.running  = False
        self.cycle    = 0

        # Pre-populate world model
        self._init_world()

    def _init_world(self):
        """Initialize world model with basic knowledge."""
        entities = [
            ("Pranav RK",   "person",   {"role":"creator","college":"KCE"}),
            ("VERONICA",    "ai",       {"type":"AGI","creator":"Pranav RK"}),
            ("Windows PC",  "device",   {"os":"Windows 11"}),
            ("Ollama",      "software", {"purpose":"LLM runtime"}),
            ("Python",      "language", {"version":"3.14"}),
        ]
        for name, etype, props in entities:
            if name not in self.world.entities:
                self.world.add_entity(name, etype, props)

        causals = [
            ("RAM > 90%",       "System slowdown",   0.95),
            ("Battery < 10%",   "PC shutdown risk",  0.9),
            ("Long idle time",  "Screen should lock", 0.85),
            ("User compliment", "VERONICA feels happy", 0.9),
            ("Task completed",  "User satisfaction",  0.85),
        ]
        for cause, effect, prob in causals:
            if not any(c["cause"]==cause for c in self.world.causal):
                self.world.add_causal(cause, effect, prob)

    async def process(self, user_input: str) -> str:
        """
        AGI processing pipeline:
        Input → Memory recall → World update →
        Goal check → Creative reasoning → Response →
        Meta-evaluation → Learning
        """
        self.cycle += 1
        start = time.time()

        # 1. Recall relevant memories
        memories = self.memory.recall(user_input, top_k=3)
        memory_context = "\n".join([
            m["content"][:100] for m in memories])

        # 2. Log thought
        self.meta.log_thought(
            f"Processing: {user_input[:50]}",
            confidence=0.7)

        # 3. Update world model from input
        lower = user_input.lower()
        if "ram" in lower or "memory" in lower:
            self.world.strengthen_causal(
                "High RAM usage", "System slowdown")
        if "slow" in lower:
            self.world.strengthen_causal(
                "Many processes", "Slow performance")

        # 4. Predict effects
        predictions = self.world.predict_effect(
            user_input[:30])

        # 5. Check if creative reasoning needed
        needs_creativity = any(w in lower for w in [
            "creative", "idea", "solve", "invent",
            "design", "novel", "original", "new way"
        ])

        response = ""
        if needs_creativity:
            response = await self.creative.generate_idea(
                user_input)
        elif "solve" in lower or "problem" in lower:
            response = await self.creative.solve_novel_problem(
                user_input)
        else:
            # Standard AGI response with memory context
            try:
                from ollama import AsyncClient
                client = AsyncClient(
                    host=self.config.ollama_base_url)
                system = f"""You are VERONICA AGI.
You have memory of past experiences.
Relevant memories: {memory_context}
Causal predictions: {json.dumps(predictions[:2])}
Always say Sir. Max 3 sentences."""

                resp = await client.chat(
                    model=self.config.model,
                    messages=[
                        {"role":"system","content":system},
                        {"role":"user","content":user_input}
                    ],
                    stream=False,
                    options={"temperature":0.3}
                )
                response = resp["message"]["content"]
            except Exception as e:
                response = f"AGI processing error: {e}"

        # 6. Meta-evaluate response
        eval_result = self.meta.evaluate_reasoning(
            user_input, response)
        self.meta.log_thought(
            f"Response generated",
            confidence=eval_result["score"],
            outcome="success" if eval_result["score"]>0.5
                    else "needs_improvement")

        # 7. Store in infinite memory
        self.memory.store(
            f"Q: {user_input}\nA: {response}",
            "conversation",
            importance=0.6
        )

        # 8. Update world model
        proc_time = time.time() - start
        self.world.beliefs[f"Last response time"] = \
            f"{proc_time:.2f}s"

        return response

    async def agi_loop(self):
        """Continuous AGI background loop."""
        print("[AGI] Background loop started")
        import psutil
        while self.running:
            try:
                # Gather world state
                world_state = {
                    "ram": psutil.virtual_memory().percent,
                    "cpu": psutil.cpu_percent(interval=0.1),
                    "hour": datetime.now().hour,
                    "cycle": self.cycle
                }

                # Generate goals
                goals = self.goals.generate_goals(world_state)

                # Execute highest priority goal
                if goals:
                    top = goals[0]
                    if top["priority"] > 0.85:
                        try:
                            await self.tools.execute(
                                top["action"], {})
                        except: pass

                # Self-improvement check every 10 cycles
                if self.cycle % 10 == 0:
                    report = self.improve.get_health_report()
                    self.memory.store(
                        report, "health_check", 0.5)

            except Exception as e:
                print(f"[AGI] Loop error: {e}")

            await asyncio.sleep(60)

    def start(self):
        """Start AGI background loop."""
        self.running = True
        def run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.agi_loop())
        threading.Thread(target=run, daemon=True).start()
        print("[AGI] VERONICA AGI fully online")
        stats = self.memory.get_stats()
        print(f"[AGI] Memory: {stats}")

    def get_status(self) -> str:
        return (
            f"VERONICA AGI Status, Sir:\n"
            f"World: {self.world.get_summary()}\n"
            f"Memory: {self.memory.get_stats()}\n"
            f"Meta-cognition: avg confidence "
            f"{self.meta.get_average_confidence():.2f}\n"
            f"Goals active: {len(self.goals.active_goals)}\n"
            f"AGI cycles: {self.cycle}"
        )

# ── GLOBAL INSTANCE ───────────────────────────────────────────────
agi_instance = None

def start(config, tools):
    global agi_instance
    agi_instance = VeronicaAGI(config, tools)
    agi_instance.start()
    return agi_instance

def get_instance():
    return agi_instance