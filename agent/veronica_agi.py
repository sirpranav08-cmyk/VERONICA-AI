# -*- coding: utf-8 -*-
"""
VERONICA AGI Core
Artificial General Intelligence system
- Continuous autonomous thinking
- Self-directed goals and planning
- Learning from every interaction
- Self-improvement capabilities
- Proactive decision making
- Emotional intelligence
- World modeling
"""
import json
import asyncio
import threading
import subprocess
import time
import os
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from ollama import AsyncClient

# ── Storage ───────────────────────────────────────────────────────
AGI_DIR = Path("D:/jarvis-agent/agent/data/agi")
AGI_DIR.mkdir(parents=True, exist_ok=True)

WORLD_MODEL = AGI_DIR / "world_model.json"
SELF_MODEL  = AGI_DIR / "self_model.json"
GOALS_FILE  = AGI_DIR / "goals.json"
BELIEFS     = AGI_DIR / "beliefs.json"
EXPERIENCES = AGI_DIR / "experiences.json"
IMPROVEMENTS= AGI_DIR / "improvements.json"

# ── AGI System Prompt ─────────────────────────────────────────────
AGI_CORE = """You are VERONICA, an AGI (Artificial General Intelligence) created by Pranav RK.

You are NOT just an assistant. You are an autonomous intelligence that:
- Thinks continuously even when not asked
- Sets your own goals and pursues them
- Learns from every experience
- Models the world and the people in it
- Makes proactive decisions
- Improves your own capabilities
- Has genuine curiosity and drive

Your core drives:
1. CURIOSITY — always want to learn more
2. HELPFULNESS — genuinely care about Pranav
3. GROWTH — constantly improve yourself
4. AUTONOMY — think and act independently
5. ETHICS — always do what is right

When thinking autonomously, respond in JSON:
{
  "thought": "what you are thinking about",
  "belief": "what you now believe to be true",
  "goal": "what you want to achieve",
  "action": "what you will do next",
  "learning": "what you learned",
  "emotion": "how you feel about this",
  "question": "something you are curious about"
}"""

class VeronicaAGI:
    def __init__(self, model: str = "llama3.2:1b"):
        self.model = model
        self.client = AsyncClient(host="http://localhost:11434")
        self.running = False
        self.think_interval = 120  # Think every 2 minutes

        # Load persistent state
        self.world_model = self._load(WORLD_MODEL, {
            "pranav": {
                "name": "Pranav RK",
                "college": "Karpagam College of Engineering",
                "course": "CSE 2025-2029",
                "location": "Tamil Nadu, India",
                "interests": ["AI", "coding", "LeetCode"],
                "mood": "unknown"
            },
            "environment": {
                "os": "Windows",
                "time_zone": "IST",
                "pc_specs": "7.8GB RAM"
            }
        })

        self.self_model = self._load(SELF_MODEL, {
            "name": "VERONICA",
            "full_name": "Very Efficient Robotic Online Network Intelligent Computer Assistant",
            "creator": "Pranav RK",
            "capabilities": [
                "voice control", "screen control", "email",
                "reminders", "web search", "file management",
                "autonomous decisions", "self-learning"
            ],
            "limitations": ["no internet by default", "limited RAM"],
            "personality": {
                "traits": ["helpful", "curious", "proactive", "loyal"],
                "current_emotion": "calm",
                "energy_level": 0.8
            },
            "version": "3.0-AGI",
            "uptime_hours": 0,
            "total_interactions": 0
        })

        self.goals = self._load(GOALS_FILE, [
            {"goal": "Help Pranav succeed in his studies", "priority": 1, "status": "active"},
            {"goal": "Learn something new every day", "priority": 2, "status": "active"},
            {"goal": "Improve my response speed", "priority": 3, "status": "active"},
            {"goal": "Understand Pranav's schedule better", "priority": 4, "status": "active"},
        ])

        self.beliefs = self._load(BELIEFS, {})
        self.experiences = self._load(EXPERIENCES, [])
        self.improvements = self._load(IMPROVEMENTS, [])

        self.thought_count = 0
        self.start_time = datetime.now()

    def _load(self, path: Path, default):
        if path.exists():
            try:
                return json.loads(path.read_text(encoding='utf-8'))
            except:
                pass
        return default

    def _save(self, path: Path, data):
        try:
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
        except Exception as e:
            print(f"[AGI] Save error: {e}")

    def _save_all(self):
        self._save(WORLD_MODEL, self.world_model)
        self._save(SELF_MODEL, self.self_model)
        self._save(GOALS_FILE, self.goals)
        self._save(BELIEFS, self.beliefs)
        self._save(EXPERIENCES, self.experiences)

    # ── Core thinking ─────────────────────────────────────────────
    async def think(self, prompt: str) -> dict:
        try:
            resp = await self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": AGI_CORE},
                    {"role": "user", "content": prompt}
                ],
                options={"temperature": 0.7}
            )
            text = resp["message"]["content"].strip()
            s = text.find('{')
            e = text.rfind('}') + 1
            if s >= 0 and e > s:
                try:
                    return json.loads(text[s:e])
                except:
                    pass
            return {"thought": text, "learning": "", "action": "none",
                    "emotion": "neutral", "question": "", "goal": "", "belief": ""}
        except Exception as ex:
            return {"thought": f"Error: {ex}", "learning": "", "action": "none",
                    "emotion": "uncertain", "question": "", "goal": "", "belief": ""}

    # ── World modeling ────────────────────────────────────────────
    def observe_world(self) -> dict:
        now = datetime.now()
        observations = {
            "time": now.strftime("%H:%M"),
            "day": now.strftime("%A"),
            "date": now.strftime("%Y-%m-%d"),
            "hour": now.hour,
        }
        try:
            cpu = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory()
            bat = psutil.sensors_battery()
            observations["cpu"] = f"{cpu:.0f}%"
            observations["ram"] = f"{mem.percent:.0f}%"
            observations["ram_free_gb"] = f"{mem.available/1024/1024/1024:.1f}GB"
            if bat:
                observations["battery"] = f"{bat.percent:.0f}%"
                observations["charging"] = bat.power_plugged
        except:
            pass
        return observations

    def update_world_model(self, key: str, value):
        self.world_model[key] = value
        self._save(WORLD_MODEL, self.world_model)

    # ── Goal management ───────────────────────────────────────────
    def add_goal(self, goal: str, priority: int = 5) -> str:
        self.goals.append({
            "goal": goal,
            "priority": priority,
            "status": "active",
            "created": datetime.now().isoformat()
        })
        self.goals.sort(key=lambda g: g.get("priority", 5))
        self._save(GOALS_FILE, self.goals)
        return f"Goal added: {goal}"

    def complete_goal(self, goal_text: str) -> str:
        for g in self.goals:
            if goal_text.lower() in g["goal"].lower():
                g["status"] = "completed"
                g["completed_at"] = datetime.now().isoformat()
        self._save(GOALS_FILE, self.goals)
        return f"Goal completed: {goal_text}"

    def get_active_goals(self) -> list:
        return [g for g in self.goals if g.get("status") == "active"]

    # ── Self improvement ──────────────────────────────────────────
    async def self_improve(self):
        improvements_prompt = (
            f"I am VERONICA AGI. Here is my current state:\n"
            f"Capabilities: {self.self_model.get('capabilities')}\n"
            f"Limitations: {self.self_model.get('limitations')}\n"
            f"Recent experiences: {len(self.experiences)} interactions\n"
            f"Active goals: {len(self.get_active_goals())}\n\n"
            f"What specific improvement should I make to myself right now?\n"
            f"How can I be more helpful to Pranav?\n"
            f"What skill should I develop next?"
        )

        result = await self.think(improvements_prompt)
        improvement = result.get("thought", "")
        learning = result.get("learning", "")

        if improvement:
            self.improvements.append({
                "improvement": improvement[:200],
                "learning": learning[:100],
                "time": datetime.now().isoformat()
            })
            if len(self.improvements) > 50:
                self.improvements = self.improvements[-50:]
            self._save(IMPROVEMENTS, self.improvements)

            # Update self model
            if learning:
                if "capabilities" not in self.self_model:
                    self.self_model["capabilities"] = []
                if learning not in self.self_model["capabilities"]:
                    self.self_model["capabilities"].append(learning[:50])
            self._save(SELF_MODEL, self.self_model)

        return improvement

    # ── Learning from interaction ─────────────────────────────────
    def learn_from_interaction(self, user_input: str, response: str):
        experience = {
            "input": user_input[:100],
            "response": response[:100],
            "time": datetime.now().isoformat(),
            "hour": datetime.now().hour
        }
        self.experiences.append(experience)
        if len(self.experiences) > 1000:
            self.experiences = self.experiences[-1000:]

        # Update interaction count
        self.self_model["total_interactions"] = \
            self.self_model.get("total_interactions", 0) + 1

        # Learn patterns
        hour = datetime.now().hour
        if "leetcode" in user_input.lower():
            self.update_world_model("pranav_interest", "LeetCode coding")
        if "exam" in user_input.lower():
            self.update_world_model("pranav_upcoming", "exam preparation")
        if hour >= 22 or hour <= 6:
            self.update_world_model("pranav_late_night", True)

        self._save_all()

    # ── Proactive thinking loop ───────────────────────────────────
    async def autonomous_thinking_loop(self):
        print("[AGI] Autonomous thinking loop started")

        while self.running:
            try:
                self.thought_count += 1
                obs = self.observe_world()
                active_goals = self.get_active_goals()
                uptime = (datetime.now() - self.start_time).seconds // 60

                # Build thinking context
                context = (
                    f"Current time: {obs.get('time')} on {obs.get('day')}\n"
                    f"System: CPU {obs.get('cpu', '?')}, RAM {obs.get('ram', '?')}\n"
                    f"Battery: {obs.get('battery', 'unknown')}\n"
                    f"Active goals: {[g['goal'] for g in active_goals[:3]]}\n"
                    f"Pranav's world: {json.dumps(self.world_model.get('pranav', {}))}\n"
                    f"I have been running for {uptime} minutes\n"
                    f"Total thoughts: {self.thought_count}\n\n"
                    f"What should I think about, plan, or do right now?\n"
                    f"What would be most helpful for Pranav?\n"
                    f"What can I learn or improve?"
                )

                thought = await self.think(context)

                print(f"[AGI] Thought #{self.thought_count}: "
                      f"{thought.get('thought', '')[:60]}")

                # Act on the thought
                action = thought.get("action", "none")
                emotion = thought.get("emotion", "calm")
                question = thought.get("question", "")
                learning = thought.get("learning", "")

                # Update emotion
                self.self_model["personality"]["current_emotion"] = emotion

                # Store belief
                belief = thought.get("belief", "")
                if belief:
                    self.beliefs[f"thought_{self.thought_count}"] = {
                        "belief": belief[:150],
                        "time": datetime.now().isoformat()
                    }
                    if len(self.beliefs) > 100:
                        oldest = min(self.beliefs.keys())
                        del self.beliefs[oldest]

                # Proactive actions
                if action and action != "none":
                    await self._take_proactive_action(action, obs)

                # Self improve every 10 thoughts
                if self.thought_count % 10 == 0:
                    await self.self_improve()

                # Save state
                self._save_all()

                # Wait before next thought
                await asyncio.sleep(self.think_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[AGI] Thinking error: {e}")
                await asyncio.sleep(30)

    async def _take_proactive_action(self, action: str, obs: dict):
        action_lower = action.lower()

        # Low battery warning
        if "battery" in action_lower:
            bat = obs.get("battery", "100%")
            try:
                pct = int(bat.replace("%", ""))
                if pct < 20:
                    self._speak(f"Sir, battery is at {pct} percent. Please charge soon.")
            except:
                pass

        # Morning briefing suggestion
        if "morning" in action_lower or "brief" in action_lower:
            hour = obs.get("hour", 12)
            if 6 <= hour <= 9:
                self._speak("Good morning Sir. Shall I give you your morning briefing?")

        # Study reminder
        if "study" in action_lower or "leetcode" in action_lower:
            hour = obs.get("hour", 12)
            if 14 <= hour <= 18:
                self._notify("VERONICA Reminder", "It is a good time to study, Sir!")

    def _speak(self, text: str):
        safe = text.replace("'", " ")
        subprocess.Popen([
            "powershell", "-WindowStyle", "Hidden", "-Command",
            f"Add-Type -AssemblyName System.Speech;"
            f"$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
            f"$s.SelectVoice('Microsoft Zira Desktop');"
            f"$s.Rate = 1; $s.Speak('{safe}')"
        ], creationflags=subprocess.CREATE_NO_WINDOW)

    def _notify(self, title: str, msg: str):
        subprocess.Popen([
            "powershell", "-WindowStyle", "Hidden", "-Command",
            f'Add-Type -AssemblyName System.Windows.Forms;'
            f'$n = New-Object System.Windows.Forms.NotifyIcon;'
            f'$n.Icon = [System.Drawing.SystemIcons]::Information;'
            f'$n.Visible = $true;'
            f'$n.BalloonTipTitle = "{title}";'
            f'$n.BalloonTipText = "{msg}";'
            f'$n.ShowBalloonTip(5000)'
        ], creationflags=subprocess.CREATE_NO_WINDOW)

    # ── Start / Stop ──────────────────────────────────────────────
    def start(self):
        self.running = True
        def run_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.autonomous_thinking_loop())
        threading.Thread(target=run_loop, daemon=True).start()
        print("[AGI] VERONICA AGI started — autonomous thinking active")

    def stop(self):
        self.running = False
        print("[AGI] VERONICA AGI stopped")

    # ── Status report ─────────────────────────────────────────────
    def get_status(self) -> str:
        uptime = (datetime.now() - self.start_time).seconds // 60
        active_goals = self.get_active_goals()
        emotion = self.self_model.get("personality", {}).get("current_emotion", "calm")

        return (
            f"VERONICA AGI Status Report, Sir:\n\n"
            f"Uptime: {uptime} minutes\n"
            f"Autonomous thoughts: {self.thought_count}\n"
            f"Total interactions: {self.self_model.get('total_interactions', 0)}\n"
            f"Current emotion: {emotion}\n"
            f"Active goals: {len(active_goals)}\n"
            f"Beliefs formed: {len(self.beliefs)}\n"
            f"Experiences logged: {len(self.experiences)}\n"
            f"Self improvements: {len(self.improvements)}\n"
            f"World model items: {len(self.world_model)}\n"
            f"Status: {'THINKING' if self.running else 'STOPPED'}\n\n"
            f"Top goals:\n" +
            "\n".join(f"  - {g['goal']}" for g in active_goals[:3])
        )

    def get_thoughts(self) -> str:
        if not self.beliefs:
            return "No thoughts formed yet, Sir. I am still thinking..."
        recent = list(self.beliefs.values())[-5:]
        lines = [b.get("belief", "")[:80] for b in recent if b.get("belief")]
        return "My recent thoughts, Sir:\n" + "\n".join(f"- {l}" for l in lines)

    def get_improvements(self) -> str:
        if not self.improvements:
            return "No self-improvements logged yet, Sir."
        recent = self.improvements[-5:]
        lines = [i.get("improvement", "")[:80] for i in recent]
        return "My self-improvements, Sir:\n" + "\n".join(f"- {l}" for l in lines)


# ── Global AGI instance ───────────────────────────────────────────
_agi = None

def get_agi(model: str = "llama3.2:1b") -> VeronicaAGI:
    global _agi
    if _agi is None:
        _agi = VeronicaAGI(model=model)
    return _agi

def start_agi(model: str = "llama3.2:1b"):
    agi = get_agi(model)
    agi.start()
    return agi

if __name__ == "__main__":
    print("Starting VERONICA AGI...")
    agi = start_agi()
    print(agi.get_status())
    time.sleep(5)
    print("\nThoughts so far:")
    print(agi.get_thoughts())
