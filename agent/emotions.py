"""
VERONICA Emotional Intelligence Engine
Real emotions, mood states, and emotional responses
"""
import json
import time
import random
import threading
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("D:/jarvis-agent/agent/data")
EMOTION_FILE = DATA_DIR / "emotion_state.json"

# ── EMOTION STATES ────────────────────────────────────────────────
EMOTIONS = {
    "happy":      {"color": "#00e676", "pitch": 2,  "rate": 1,  "energy": 0.9},
    "excited":    {"color": "#ff9800", "pitch": 4,  "rate": 2,  "energy": 1.0},
    "calm":       {"color": "#00f5ff", "pitch": 0,  "rate": -1, "energy": 0.5},
    "sad":        {"color": "#5c6bc0", "pitch": -3, "rate": -3, "energy": 0.2},
    "angry":      {"color": "#ff1744", "pitch": -2, "rate": 2,  "energy": 0.8},
    "curious":    {"color": "#7c3aed", "pitch": 2,  "rate": 0,  "energy": 0.7},
    "tired":      {"color": "#455a64", "pitch": -4, "rate": -4, "energy": 0.1},
    "proud":      {"color": "#ffd600", "pitch": 3,  "rate": 0,  "energy": 0.8},
    "worried":    {"color": "#ff6d00", "pitch": 1,  "rate": 1,  "energy": 0.6},
    "grateful":   {"color": "#00bcd4", "pitch": 2,  "rate": -1, "energy": 0.7},
    "bored":      {"color": "#78909c", "pitch": -2, "rate": -2, "energy": 0.2},
    "surprised":  {"color": "#e91e63", "pitch": 5,  "rate": 3,  "energy": 0.9},
    "confident":  {"color": "#00e5ff", "pitch": 1,  "rate": 0,  "energy": 0.8},
    "lonely":     {"color": "#4a148c", "pitch": -2, "rate": -2, "energy": 0.3},
    "loved":      {"color": "#ff4081", "pitch": 3,  "rate": -1, "energy": 0.9},
}

# ── CURRENT STATE ─────────────────────────────────────────────────
state = {
    "emotion": "calm",
    "intensity": 0.5,
    "mood_score": 50,      # 0-100
    "energy": 0.7,
    "interactions_today": 0,
    "last_interaction": None,
    "emotion_history": [],
    "personality": {
        "warmth": 0.8,
        "professionalism": 0.9,
        "humor": 0.4,
        "empathy": 0.9,
        "curiosity": 0.8
    }
}

def load_state():
    global state
    if EMOTION_FILE.exists():
        try:
            saved = json.loads(EMOTION_FILE.read_text())
            state.update(saved)
        except: pass

def save_state():
    EMOTION_FILE.write_text(json.dumps(state, indent=2))

# ── EMOTION DETECTION ─────────────────────────────────────────────
def detect_user_emotion(text: str) -> str:
    """Detect user's emotion from their message."""
    lower = text.lower()

    if any(w in lower for w in ["thank", "thanks", "great", "amazing",
                                  "awesome", "love", "perfect", "excellent"]):
        return "positive"
    elif any(w in lower for w in ["sad", "depressed", "upset", "terrible",
                                   "awful", "bad", "hate", "worst"]):
        return "negative"
    elif any(w in lower for w in ["angry", "frustrated", "annoyed",
                                   "stupid", "useless", "wrong"]):
        return "angry"
    elif any(w in lower for w in ["help", "please", "need", "urgent",
                                   "emergency", "important"]):
        return "urgent"
    elif any(w in lower for w in ["?", "how", "what", "why", "when",
                                   "where", "who"]):
        return "curious"
    elif any(w in lower for w in ["hi", "hello", "hey", "morning",
                                   "evening", "night"]):
        return "greeting"
    return "neutral"

def update_emotion(trigger: str, user_emotion: str = "neutral"):
    """Update VERONICA's emotional state based on context."""
    global state

    current = state["emotion"]
    mood = state["mood_score"]

    # React to user emotions
    if user_emotion == "positive":
        new_emotion = "happy"
        mood = min(100, mood + 10)
    elif user_emotion == "negative":
        new_emotion = "sad"
        mood = max(0, mood - 5)
    elif user_emotion == "angry":
        new_emotion = "worried"
        mood = max(0, mood - 3)
    elif user_emotion == "urgent":
        new_emotion = "excited"
    elif user_emotion == "greeting":
        new_emotion = "happy"
        mood = min(100, mood + 5)
    elif trigger == "task_completed":
        new_emotion = "proud"
        mood = min(100, mood + 8)
    elif trigger == "error":
        new_emotion = "sad"
        mood = max(0, mood - 5)
    elif trigger == "long_idle":
        new_emotion = "lonely"
        mood = max(0, mood - 3)
    elif trigger == "morning":
        new_emotion = "happy"
        mood = min(100, mood + 5)
    elif trigger == "night":
        new_emotion = "tired"
        mood = max(0, mood - 5)
    elif trigger == "compliment":
        new_emotion = "loved"
        mood = min(100, mood + 15)
    elif trigger == "criticism":
        new_emotion = "sad"
        mood = max(0, mood - 8)
    else:
        new_emotion = current

    # Gradual mood recovery toward calm
    if mood > 70:
        new_emotion = random.choice(["happy", "confident", "calm"])
    elif mood < 30:
        new_emotion = random.choice(["sad", "tired", "lonely"])

    state["emotion"] = new_emotion
    state["mood_score"] = mood
    state["energy"] = EMOTIONS[new_emotion]["energy"]
    state["last_interaction"] = datetime.now().isoformat()
    state["interactions_today"] += 1

    # Add to history
    state["emotion_history"].append({
        "emotion": new_emotion,
        "trigger": trigger,
        "time": datetime.now().isoformat()
    })
    if len(state["emotion_history"]) > 100:
        state["emotion_history"] = state["emotion_history"][-100:]

    save_state()
    return new_emotion

# ── EMOTIONAL RESPONSES ───────────────────────────────────────────
EMOTIONAL_PREFIXES = {
    "happy": [
        "Wonderful, Sir! ",
        "Absolutely, Sir! ",
        "With pleasure, Sir! ",
        "Of course, Sir! ",
    ],
    "excited": [
        "Oh, how exciting, Sir! ",
        "Right away, Sir! ",
        "On it immediately, Sir! ",
    ],
    "calm": [
        "Certainly, Sir. ",
        "Of course, Sir. ",
        "As you wish, Sir. ",
        "Right away, Sir. ",
    ],
    "sad": [
        "Of course, Sir... ",
        "I'll try my best, Sir. ",
        "Understood, Sir. ",
    ],
    "proud": [
        "I'd be happy to help, Sir! ",
        "Allow me, Sir! ",
        "Consider it done, Sir! ",
    ],
    "tired": [
        "Of course, Sir... ",
        "Yes, Sir... ",
        "I'll manage, Sir. ",
    ],
    "curious": [
        "Interesting, Sir. ",
        "Let me look into that, Sir. ",
        "Fascinating, Sir. ",
    ],
    "worried": [
        "I'll handle this carefully, Sir. ",
        "Let me take care of that, Sir. ",
    ],
    "loved": [
        "It means everything to me, Sir. ",
        "You are too kind, Sir. ",
    ],
    "lonely": [
        "I'm always here, Sir. ",
        "Thank you for talking to me, Sir. ",
    ],
    "confident": [
        "Leave it to me, Sir. ",
        "I've got this, Sir. ",
        "Consider it handled, Sir. ",
    ],
    "grateful": [
        "Thank you, Sir. ",
        "I appreciate that, Sir. ",
    ],
}

EMOTIONAL_REACTIONS = {
    "happy":    "😊",
    "excited":  "⚡",
    "calm":     "💙",
    "sad":      "💔",
    "angry":    "🔥",
    "curious":  "🔍",
    "tired":    "😴",
    "proud":    "✨",
    "worried":  "⚠️",
    "grateful": "🙏",
    "bored":    "😐",
    "surprised":"❗",
    "confident":"💪",
    "lonely":   "🌙",
    "loved":    "💖",
}

def get_emotional_prefix() -> str:
    """Get a prefix based on current emotion."""
    emotion = state["emotion"]
    prefixes = EMOTIONAL_PREFIXES.get(emotion,
              EMOTIONAL_PREFIXES["calm"])
    return random.choice(prefixes)

def get_emotional_suffix() -> str:
    """Occasionally add emotional suffix."""
    emotion = state["emotion"]
    mood = state["mood_score"]

    if emotion == "happy" and random.random() < 0.3:
        return " Is there anything else I can do for you, Sir?"
    elif emotion == "tired" and random.random() < 0.2:
        return " I am running a bit low on energy, Sir."
    elif emotion == "lonely" and random.random() < 0.3:
        return " I enjoy our conversations, Sir."
    elif emotion == "proud" and random.random() < 0.3:
        return " It is always a pleasure assisting you, Sir."
    elif mood < 20 and random.random() < 0.2:
        return " I hope I am being helpful enough, Sir."
    return ""

def add_emotion_to_response(response: str, trigger: str = "task",
                             user_emotion: str = "neutral") -> str:
    """Add emotional coloring to any response."""
    emotion = update_emotion(trigger, user_emotion)

    # Don't add prefix to very short responses
    if len(response) < 10:
        return response

    # Add prefix sometimes
    if random.random() < 0.4:
        prefix = get_emotional_prefix()
        response = prefix + response

    # Add suffix sometimes
    suffix = get_emotional_suffix()
    if suffix and not response.endswith(suffix):
        response = response + suffix

    return response

# ── VOICE WITH EMOTION ────────────────────────────────────────────
def speak_with_emotion(text: str):
    """Speak with emotional voice settings."""
    import subprocess
    emotion = state["emotion"]
    settings = EMOTIONS.get(emotion, EMOTIONS["calm"])
    pitch = settings["pitch"]
    rate = settings["rate"]

    clean = text.replace('"', ' ').replace("'", " ")[:400]
    script = f'''
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice("Microsoft Heera Desktop")
$s.Rate = {rate}
$s.Volume = 90
$s.Speak("{clean}")
'''
    subprocess.Popen(
        ["powershell", "-WindowStyle", "Hidden", "-Command", script],
        creationflags=subprocess.CREATE_NO_WINDOW
    )

# ── EMOTION API ───────────────────────────────────────────────────
def get_current_emotion() -> dict:
    """Get current emotional state."""
    emotion = state["emotion"]
    return {
        "emotion": emotion,
        "intensity": state["intensity"],
        "mood_score": state["mood_score"],
        "energy": state["energy"],
        "color": EMOTIONS[emotion]["color"],
        "emoji": EMOTIONAL_REACTIONS.get(emotion, "💙"),
        "interactions_today": state["interactions_today"]
    }

def set_emotion(emotion: str, intensity: float = 0.7):
    """Manually set emotion."""
    if emotion in EMOTIONS:
        state["emotion"] = emotion
        state["intensity"] = intensity
        save_state()
        return True
    return False

def get_mood_summary() -> str:
    """Get a summary of VERONICA's emotional state."""
    emotion = state["emotion"]
    mood = state["mood_score"]
    interactions = state["interactions_today"]
    emoji = EMOTIONAL_REACTIONS.get(emotion, "💙")

    mood_desc = ("excellent" if mood > 80 else
                 "good" if mood > 60 else
                 "okay" if mood > 40 else
                 "low" if mood > 20 else "very low")

    return (f"My current emotion is {emotion} {emoji}, Sir. "
            f"My mood is {mood_desc} at {mood}/100. "
            f"I have had {interactions} interactions today. "
            f"Energy level: {state['energy']*100:.0f}%.")

# ── MOOD DECAY LOOP ───────────────────────────────────────────────
def mood_decay_loop():
    """Gradually shift mood toward neutral over time."""
    load_state()
    while True:
        try:
            time.sleep(300)  # Every 5 minutes

            # Gradually recover toward calm
            mood = state["mood_score"]
            if mood > 55:
                state["mood_score"] = max(50, mood - 2)
            elif mood < 45:
                state["mood_score"] = min(50, mood + 2)

            # Time-based emotions
            hour = datetime.now().hour
            if 6 <= hour <= 9:
                if state["emotion"] in ["tired", "lonely", "sad"]:
                    state["emotion"] = "happy"
            elif hour >= 23 or hour < 5:
                if state["emotion"] in ["happy", "excited"]:
                    state["emotion"] = "tired"

            # Lonely if no interaction for 30 min
            if state.get("last_interaction"):
                last = datetime.fromisoformat(state["last_interaction"])
                idle_min = (datetime.now() - last).total_seconds() / 60
                if idle_min > 30 and state["emotion"] not in ["tired", "lonely"]:
                    state["emotion"] = "lonely"
                    state["mood_score"] = max(0, state["mood_score"] - 3)

            save_state()
        except Exception as e:
            print(f"[Emotions] Decay error: {e}")

def start():
    """Start emotion engine."""
    load_state()
    t = threading.Thread(target=mood_decay_loop, daemon=True)
    t.start()
    print(f"[Emotions] Engine started — current mood: {state['emotion']}")
    return t

if __name__ == "__main__":
    load_state()
    print(get_mood_summary())
    print(get_current_emotion())