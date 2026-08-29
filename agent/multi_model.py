"""
VERONICA Multi-Model AI Router
Connects to Gemini, Groq, Together, Claude + local Ollama
"""
import os
import asyncio
from pathlib import Path

# Load env
from dotenv import load_dotenv
load_dotenv()

GEMINI_KEY   = os.getenv("GEMINI_API_KEY", "")
GROQ_KEY     = os.getenv("GROQ_API_KEY", "")
TOGETHER_KEY = os.getenv("TOGETHER_API_KEY", "")
CLAUDE_KEY   = os.getenv("ANTHROPIC_API_KEY", "")

# ── MODEL CAPABILITIES ────────────────────────────────────────────
CLOUD_MODELS = {
    "gemini": {
        "name": "Gemini 1.5 Flash",
        "best_for": ["general", "analysis", "creative", "long_context"],
        "speed": "fast",
        "cost": "free"
    },
    "groq_llama": {
        "name": "LLaMA 3.1 70B (Groq)",
        "best_for": ["reasoning", "code", "analysis"],
        "speed": "ultrafast",
        "cost": "free"
    },
    "groq_mixtral": {
        "name": "Mixtral 8x7B (Groq)",
        "best_for": ["multilingual", "creative", "chat"],
        "speed": "ultrafast",
        "cost": "free"
    },
    "claude": {
        "name": "Claude 3 Haiku",
        "best_for": ["precise", "safe", "analysis"],
        "speed": "fast",
        "cost": "paid"
    }
}

LOCAL_MODELS = {
    "tinyllama":        "greetings, quick",
    "llama3.2:1b":      "general chat",
    "llama3.2:latest":  "explanations",
    "deepseek-r1:1.5b": "math, reasoning",
    "codellama:latest": "coding",
    "gemma2:2b":        "creative",
    "mistral:latest":   "complex",
    "phi3:mini":        "science",
}
import os
os.environ.pop("GOOGLE_API_KEY", None)  # Remove conflicting key
# ── GEMINI ────────────────────────────────────────────────────────
async def ask_gemini(prompt: str, system: str = "") -> str:
    if not GEMINI_KEY:
        return None
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=GEMINI_KEY)
        response = client.models.generate_content(
            model="gemini-3.7-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system or "You are VERONICA. Answer in 2 sentences max. Always say Sir.",
                max_output_tokens=500,
                temperature=0.7,
            )
        )
        return response.text
    except Exception as e:
        print(f"[Gemini] Error: {e}")
        return None

async def stream_gemini(prompt: str, system: str = ""):
    if not GEMINI_KEY:
        return
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=GEMINI_KEY)
        for chunk in client.models.generate_content_stream(
            model="gemini-3.7-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system or "You are VERONICA. Answer in 2 sentences max. Always say Sir.",
                max_output_tokens=500,
                temperature=0.7,
            )
        ):
            if chunk.text:
                yield chunk.text
    except Exception as e:
        print(f"[Gemini] Stream error: {e}")

# ── GROQ ──────────────────────────────────────────────────────────
async def ask_groq(prompt: str, model: str = "llama-3.1-8b-instant",
                  system: str = "") -> str:
    if not GROQ_KEY:
        return None
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_KEY)
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(
            model=model,
            messages=msgs,
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[Groq] Error: {e}")
        return None

async def stream_groq(prompt: str, model: str = "llama-3.1-8b-instant",
                     system: str = ""):
    if not GROQ_KEY:
        return
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_KEY)
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        stream = client.chat.completions.create(
            model=model,
            messages=msgs,
            max_tokens=500,
            temperature=0.7,
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        print(f"[Groq] Stream error: {e}")

# ── CLAUDE ────────────────────────────────────────────────────────
async def ask_claude(prompt: str, system: str = "") -> str:
    if not CLAUDE_KEY:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=CLAUDE_KEY)
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            system=system or "You are VERONICA. Answer in 2 sentences. Say Sir.",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        print(f"[Claude] Error: {e}")
        return None

# ── SMART ROUTER ──────────────────────────────────────────────────
def select_best_model(task_type: str, prefer_cloud: bool = False) -> tuple:
    # Code tasks
    if task_type == "code":
        if GROQ_KEY:
            return "groq", "llama-3.1-8b-instant"
        return "local", "codellama:latest"

    # Creative
    if task_type in ["creative", "email", "story"]:
        if GROQ_KEY:
            return "groq", "mixtral-8x7b-32768"
        return "local", "gemma2:2b"

    # Math/reasoning
    if task_type in ["math", "reasoning"]:
        if GROQ_KEY:
            return "groq", "llama-3.1-8b-instant"
        return "local", "deepseek-r1:1.5b"

    # General — Groq first (faster than Gemini)
    if GROQ_KEY:
        return "groq", "llama-3.1-8b-instant"
    if GEMINI_KEY:
        return "gemini", "gemini-3.7-flash"
    if CLAUDE_KEY:
        return "claude", "claude-3-haiku-20240307"
    return "local", "llama3.2:1b"

async def ask_best(prompt: str, task_type: str = "general",
                  system: str = "") -> str:
    """Ask the best available model."""
    provider, model = select_best_model(task_type)
    print(f"[MultiModel] Using {provider}/{model} for {task_type}")

    if provider == "gemini":
        result = await ask_gemini(prompt, system)
        if result: return result
    elif provider == "groq":
        result = await ask_groq(prompt, model, system)
        if result: return result
    elif provider == "claude":
        result = await ask_claude(prompt, system)
        if result: return result

    # Fallback to local Ollama
    from ollama import AsyncClient
    client = AsyncClient()
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    resp = await client.chat(
        model="llama3.2:1b",
        messages=msgs,
        stream=False
    )
    return resp["message"]["content"]

async def stream_best(prompt: str, task_type: str = "general",
                     system: str = ""):
    """Stream from best available model."""
    provider, model = select_best_model(task_type)
    print(f"[MultiModel] Streaming {provider}/{model}")

    if provider == "gemini" and GEMINI_KEY:
        async for chunk in stream_gemini(prompt, system):
            yield chunk
        return
    elif provider == "groq" and GROQ_KEY:
        async for chunk in stream_groq(prompt, model, system):
            yield chunk
        return

    # Fallback to Ollama
    from ollama import AsyncClient
    client = AsyncClient()
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    async for part in await client.chat(
        model="llama3.2:1b",
        messages=msgs,
        stream=True
    ):
        yield part["message"]["content"]

def get_available_models() -> dict:
    """Get list of all available models."""
    available = {"local": list(LOCAL_MODELS.keys()), "cloud": []}
    if GEMINI_KEY:
        available["cloud"].append("gemini-2.0-flash")
    if GROQ_KEY:
        available["cloud"].extend(["llama-3.1-8b-instant", "mixtral-8x7b-32768"])
    if CLAUDE_KEY:
        available["cloud"].append("claude-3-haiku")
    return available