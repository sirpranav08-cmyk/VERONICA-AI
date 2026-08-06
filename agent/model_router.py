"""
VERONICA Model Router
Automatically picks the best AI model for each task
Uses all installed models intelligently
"""

MODEL_ROUTES = {
    # Ultra fast — greetings, simple commands
    "greeting":  "tinyllama",
    "time":      "tinyllama",
    "reminder":  "tinyllama",
    "system":    "tinyllama",

    # General chat
    "chat":      "llama3.2:latest",
    "question":  "llama3.2:latest",
    "explain":   "llama3.2:latest",

    # Deep reasoning & math
    "math":      "deepseek-r1:1.5b",
    "logic":     "deepseek-r1:1.5b",
    "analyze":   "deepseek-r1:1.5b",
    "plan":      "deepseek-r1:1.5b",
    "research":  "deepseek-r1:1.5b",

    # Code
    "code":      "deepseek-r1:1.5b",
    "debug":     "deepseek-r1:1.5b",
    "program":   "deepseek-r1:1.5b",
    "function":  "deepseek-r1:1.5b",
    "algorithm": "deepseek-r1:1.5b",

    # Creative writing
    "write":     "gemma2:2b",
    "story":     "gemma2:2b",
    "poem":      "gemma2:2b",
    "creative":  "gemma2:2b",
    "email":     "gemma2:2b",
    "essay":     "gemma2:2b",

    # Complex / long tasks
    "complex":   "mistral:latest",
    "long":      "mistral:latest",
    "detailed":  "mistral:latest",

    # Science / technical
    "science":   "phi3:mini",
    "technical": "phi3:mini",
    "medical":   "phi3:mini",
}

DEFAULT_MODEL = "deepseek-r1:1.5b"

# All available models
AVAILABLE_MODELS = [
    "tinyllama",
    "deepseek-r1:1.5b",
    "llama3.2:latest",
    "deepseek-r1:1.5b",
    "codellama:latest",
    "gemma2:2b",
    "mistral:latest",
    "phi3:mini",
]

def detect_model(text: str) -> str:
    """Detect best model from user input."""
    lower = text.lower()

    # ── Greetings / simple ───────────────────────────────────────
    if any(w in lower for w in ["hi", "hello", "hey", "thanks", "bye",
                                  "good morning", "good night", "good afternoon"]):
        return MODEL_ROUTES["greeting"]

    # ── Time / reminders ─────────────────────────────────────────
    if any(w in lower for w in ["time", "date", "reminder", "remind",
                                  "alarm", "schedule", "task"]):
        return MODEL_ROUTES["reminder"]

    # ── System commands ──────────────────────────────────────────
    if any(w in lower for w in ["cpu", "ram", "system", "memory",
                                  "disk", "screenshot", "battery"]):
        return MODEL_ROUTES["system"]

    # ── Code ─────────────────────────────────────────────────────
    if any(w in lower for w in ["code", "program", "function", "debug",
                                  "error", "python", "javascript", "java",
                                  "html", "css", "leetcode", "algorithm",
                                  "script", "class", "method", "syntax",
                                  "compile", "runtime", "variable", "loop",
                                  "array", "list", "sort", "search"]):
        return MODEL_ROUTES["code"]

    # ── Math / Reasoning ─────────────────────────────────────────
    if any(w in lower for w in ["calculate", "math", "solve", "equation",
                                  "logic", "analyze", "why", "how does",
                                  "explain why", "proof", "theorem", "formula",
                                  "percentage", "statistics", "probability"]):
        return MODEL_ROUTES["math"]

    # ── Creative writing ─────────────────────────────────────────
    if any(w in lower for w in ["write a story", "write a poem", "essay",
                                  "letter", "compose", "creative", "draft",
                                  "fiction", "narrative", "lyrics"]):
        return MODEL_ROUTES["write"]

    # ── Email ────────────────────────────────────────────────────
    if any(w in lower for w in ["email", "send email", "reply email",
                                  "compose email", "write email"]):
        return MODEL_ROUTES["email"]

    # ── Science / Technical ──────────────────────────────────────
    if any(w in lower for w in ["science", "physics", "chemistry", "biology",
                                  "engineering", "medical", "disease", "medicine",
                                  "technology", "quantum", "neural", "AI"]):
        return MODEL_ROUTES["science"]

    # ── Complex / detailed ───────────────────────────────────────
    if any(w in lower for w in ["explain in detail", "detailed explanation",
                                  "comprehensive", "in depth", "elaborate",
                                  "step by step"]):
        return MODEL_ROUTES["complex"]

    # ── Planning ─────────────────────────────────────────────────
    if any(w in lower for w in ["plan", "strategy", "roadmap", "steps",
                                  "how to", "guide", "tutorial"]):
        return MODEL_ROUTES["plan"]

    # ── Research ─────────────────────────────────────────────────
    if any(w in lower for w in ["research", "find out", "investigate",
                                  "compare", "difference between", "vs"]):
        return MODEL_ROUTES["research"]

    return DEFAULT_MODEL


def get_model_info(model: str) -> str:
    """Get model description."""
    info = {
        "tinyllama":        "TinyLlama 1.1B — Ultra fast, simple tasks",
        "deepseek-r1:1.5b":      "LLaMA 3.2 1B — Fast general intelligence",
        "llama3.2:latest":  "LLaMA 3.2 3B — Smart general intelligence",
        "deepseek-r1:1.5b": "DeepSeek R1 1.5B — Deep reasoning & math",
        "codellama:latest": "CodeLlama 7B — Code specialist",
        "gemma2:2b":        "Gemma2 2B — Creative writing",
        "mistral:latest":   "Mistral 7B — Complex detailed tasks",
        "phi3:mini":        "Phi3 Mini — Science & technical",
    }
    return info.get(model, model)


if __name__ == "__main__":
    tests = [
        "hi veronica",
        "write a python function to sort a list",
        "what is 25 * 48",
        "write a poem about AI",
        "what time is it",
        "send email to my friend",
        "explain recursion",
        "write a java code",
        "what is quantum physics",
        "plan my week",
    ]
    print("VERONICA Model Router Test")
    print("-" * 40)
    for t in tests:
        m = detect_model(t)
        info = get_model_info(m)
        print(f"Input: '{t}'")
        print(f"Model: {m} ({info})")
        print()