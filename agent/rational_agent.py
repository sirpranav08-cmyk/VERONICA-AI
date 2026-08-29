"""
VERONICA Rational Agent
Based on AI rational agent theory:
- Percepts → State → Goals → Actions → Utility
- Always chooses the action with highest expected utility
- Learns from outcomes to improve future decisions
"""
import json
import asyncio
import time
from datetime import datetime
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path("D:/jarvis-agent/agent/data")
RATIONAL_FILE = DATA_DIR / "rational_state.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── PERCEPT SYSTEM ────────────────────────────────────────────────
class Percept:
    """What VERONICA perceives from the environment."""
    def __init__(self):
        self.time = datetime.now()
        self.cpu = 0
        self.ram = 0
        self.battery = 100
        self.user_present = False
        self.last_command = ""
        self.error_count = 0
        self.idle_minutes = 0
        self.active_app = ""

    def gather(self) -> dict:
        """Gather all environment percepts."""
        import psutil, ctypes

        # System state
        try:
            self.cpu = psutil.cpu_percent(interval=0.1)
            self.ram = psutil.virtual_memory().percent
            bat = psutil.sensors_battery()
            self.battery = bat.percent if bat else 100
        except: pass

        # Idle time
        try:
            class LII(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_uint),
                           ("dwTime", ctypes.c_uint)]
            lii = LII()
            lii.cbSize = ctypes.sizeof(LII)
            ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
            millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
            self.idle_minutes = millis / 60000
        except: pass

        return {
            "time": self.time.isoformat(),
            "hour": self.time.hour,
            "cpu": self.cpu,
            "ram": self.ram,
            "battery": self.battery,
            "idle_minutes": self.idle_minutes,
            "day": self.time.strftime("%A")
        }

# ── STATE REPRESENTATION ──────────────────────────────────────────
class WorldState:
    """VERONICA's internal model of the world."""
    def __init__(self):
        self.percepts = {}
        self.history = []
        self.beliefs = {}
        self.load()

    def load(self):
        if RATIONAL_FILE.exists():
            try:
                data = json.loads(RATIONAL_FILE.read_text())
                self.beliefs = data.get("beliefs", {})
            except: pass

    def save(self):
        RATIONAL_FILE.write_text(json.dumps({
            "beliefs": self.beliefs,
            "updated": datetime.now().isoformat()
        }, indent=2))

    def update(self, percepts: dict):
        """Update world state from new percepts."""
        self.percepts = percepts
        self.history.append(percepts)
        if len(self.history) > 100:
            self.history = self.history[-100:]

        # Update beliefs
        self.beliefs["last_cpu"] = percepts.get("cpu", 0)
        self.beliefs["last_ram"] = percepts.get("ram", 0)
        self.beliefs["last_battery"] = percepts.get("battery", 100)
        self.beliefs["peak_hour"] = percepts.get("hour", 9)
        self.save()

    def is_system_stressed(self) -> bool:
        return (self.percepts.get("cpu", 0) > 80 or
                self.percepts.get("ram", 0) > 85)

    def is_battery_critical(self) -> bool:
        return self.percepts.get("battery", 100) < 15

    def is_user_idle(self) -> bool:
        return self.percepts.get("idle_minutes", 0) > 10

    def is_work_hours(self) -> bool:
        hour = self.percepts.get("hour", 12)
        return 9 <= hour <= 17

    def is_night(self) -> bool:
        hour = self.percepts.get("hour", 12)
        return hour >= 22 or hour < 6

# ── GOAL SYSTEM ───────────────────────────────────────────────────
class Goal:
    """A goal with priority and conditions."""
    def __init__(self, name: str, priority: float,
                 condition, action: str, args: dict = {}):
        self.name = name
        self.priority = priority  # 0.0 to 1.0
        self.condition = condition  # function(state) -> bool
        self.action = action
        self.args = args
        self.last_triggered = 0
        self.cooldown = 300  # seconds

    def is_active(self, state: WorldState) -> bool:
        """Check if goal condition is met."""
        now = time.time()
        if now - self.last_triggered < self.cooldown:
            return False
        return self.condition(state)

    def trigger(self):
        self.last_triggered = time.time()

# ── UTILITY FUNCTION ──────────────────────────────────────────────
class UtilityFunction:
    """Calculates utility of actions."""
    def __init__(self):
        self.action_history = defaultdict(list)
        self.load_history()

    def load_history(self):
        history_file = DATA_DIR / "utility_history.json"
        if history_file.exists():
            try:
                data = json.loads(history_file.read_text())
                self.action_history = defaultdict(list, data)
            except: pass

    def save_history(self):
        history_file = DATA_DIR / "utility_history.json"
        history_file.write_text(json.dumps(
            dict(self.action_history), indent=2))

    def calculate(self, action: str, state: WorldState,
                 goal: Goal) -> float:
        """Calculate expected utility of taking an action."""
        base_utility = goal.priority

        # Adjust based on past success
        history = self.action_history.get(action, [])
        if history:
            success_rate = sum(history) / len(history)
            base_utility *= (0.5 + success_rate * 0.5)

        # Time-based adjustments
        hour = state.percepts.get("hour", 12)
        if 9 <= hour <= 17:  # Work hours — boost productivity
            if action in ["activate_mode", "open_app", "get_reminders"]:
                base_utility *= 1.2
        elif hour >= 22:  # Night — boost rest actions
            if action in ["lock_screen", "sleep_pc", "activate_mode"]:
                base_utility *= 1.3

        # System stress adjustments
        if state.is_system_stressed():
            if action == "kill_process":
                base_utility *= 1.5

        return min(1.0, base_utility)

    def record_outcome(self, action: str, success: bool):
        """Record action outcome for learning."""
        self.action_history[action].append(1.0 if success else 0.0)
        if len(self.action_history[action]) > 50:
            self.action_history[action] = self.action_history[action][-50:]
        self.save_history()

# ── RATIONAL AGENT ────────────────────────────────────────────────
class RationalAgent:
    def __init__(self, tools):
        self.tools = tools
        self.percept = Percept()
        self.state = WorldState()
        self.utility = UtilityFunction()
        self.goals = self._define_goals()
        self.action_queue = []
        self.decisions_made = []

    def _define_goals(self) -> list:
        """Define all agent goals with priorities."""
        return [
            # Critical goals — highest priority
            Goal(
                name="Prevent data loss — critical RAM",
                priority=0.95,
                condition=lambda s: s.percepts.get("ram", 0) > 90,
                action="kill_process",
                args={"name": "chrome.exe"}
            ),
            Goal(
                name="Protect battery — critical level",
                priority=0.95,
                condition=lambda s: s.is_battery_critical(),
                action="set_brightness",
                args={"level": 20}
            ),
            Goal(
                name="Security — auto lock idle screen",
                priority=0.85,
                condition=lambda s: s.is_user_idle(),
                action="lock_screen",
                args={}
            ),
            Goal(
                name="Performance — high RAM warning",
                priority=0.75,
                condition=lambda s: 80 < s.percepts.get("ram", 0) <= 90,
                action="system_info",
                args={}
            ),
            Goal(
                name="Productivity — start work mode",
                priority=0.65,
                condition=lambda s: (s.percepts.get("hour") == 9 and
                                    s.percepts.get("idle_minutes", 99) < 5),
                action="activate_mode",
                args={"mode": "work"}
            ),
            Goal(
                name="Rest — suggest sleep at night",
                priority=0.60,
                condition=lambda s: s.is_night(),
                action="activate_mode",
                args={"mode": "sleep"}
            ),
            Goal(
                name="Awareness — morning briefing",
                priority=0.55,
                condition=lambda s: (7 <= s.percepts.get("hour", 0) <= 8 and
                                    s.percepts.get("idle_minutes", 99) < 2),
                action="get_reminders",
                args={}
            ),
        ]

    def perceive(self) -> dict:
        """Gather percepts from environment."""
        percepts = self.percept.gather()
        self.state.update(percepts)
        return percepts

    def select_action(self) -> tuple:
        """
        Core rational decision making:
        Select action with highest expected utility.
        """
        active_goals = []
        for goal in self.goals:
            if goal.is_active(self.state):
                utility = self.utility.calculate(
                    goal.action, self.state, goal)
                active_goals.append((utility, goal))

        if not active_goals:
            return None, None

        # Sort by utility — pick highest
        active_goals.sort(key=lambda x: x[0], reverse=True)
        best_utility, best_goal = active_goals[0]

        return best_goal, best_utility

    async def act(self, goal: Goal) -> bool:
        """Execute the selected action."""
        try:
            result = await self.tools.execute(
                goal.action, goal.args)
            goal.trigger()

            # Record decision
            self.decisions_made.append({
                "goal": goal.name,
                "action": goal.action,
                "result": str(result)[:100],
                "time": datetime.now().isoformat(),
                "success": True
            })

            # Learn from outcome
            self.utility.record_outcome(goal.action, True)

            # Notify user
            self._notify(goal.name, str(result)[:100])

            print(f"[Rational] Action: {goal.name}")
            return True

        except Exception as e:
            self.utility.record_outcome(goal.action, False)
            self.decisions_made.append({
                "goal": goal.name,
                "action": goal.action,
                "result": str(e)[:100],
                "time": datetime.now().isoformat(),
                "success": False
            })
            return False

    def _notify(self, title: str, message: str):
        """Send Windows notification."""
        import subprocess
        script = f'''
Add-Type -AssemblyName System.Windows.Forms
$n = New-Object System.Windows.Forms.NotifyIcon
$n.Icon = [System.Drawing.SystemIcons]::Information
$n.Visible = $true
$n.BalloonTipTitle = "VERONICA — {title[:30]}"
$n.BalloonTipText = "{message[:100]}"
$n.ShowBalloonTip(4000)
'''
        subprocess.Popen(
            ["powershell", "-WindowStyle", "Hidden", "-Command", script],
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    async def run_cycle(self):
        """Run one perceive-think-act cycle."""
        # Perceive
        percepts = self.perceive()

        # Think — select best action
        goal, utility = self.select_action()

        if goal and utility > 0.3:
            print(f"[Rational] Goal: {goal.name} "
                 f"(utility={utility:.2f})")
            # Act
            await self.act(goal)

    def get_state_summary(self) -> str:
        """Get readable state summary."""
        p = self.state.percepts
        return (
            f"Rational Agent State, Sir:\n"
            f"CPU: {p.get('cpu', 0):.0f}% | "
            f"RAM: {p.get('ram', 0):.0f}% | "
            f"Battery: {p.get('battery', 100):.0f}%\n"
            f"System stressed: {self.state.is_system_stressed()}\n"
            f"User idle: {p.get('idle_minutes', 0):.1f} min\n"
            f"Active goals: {sum(1 for g in self.goals if g.is_active(self.state))}\n"
            f"Decisions made: {len(self.decisions_made)}"
        )

    def get_recent_decisions(self, n: int = 5) -> list:
        return self.decisions_made[-n:]

# ── BACKGROUND LOOP ───────────────────────────────────────────────
rational_agent_instance = None

async def rational_loop(agent: RationalAgent):
    """Run rational agent loop every 30 seconds."""
    print("[Rational] Agent loop started")
    while True:
        try:
            await agent.run_cycle()
        except Exception as e:
            print(f"[Rational] Loop error: {e}")
        await asyncio.sleep(30)

def start(tools):
    """Start rational agent in background."""
    global rational_agent_instance
    rational_agent_instance = RationalAgent(tools)

    import threading

    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            rational_loop(rational_agent_instance))

    t = threading.Thread(target=run, daemon=True)
    t.start()
    print("[Rational] Rational agent started")
    return rational_agent_instance

def get_instance():
    return rational_agent_instance