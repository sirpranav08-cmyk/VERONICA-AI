from dataclasses import dataclass

@dataclass
class Config:
    model: str = "phi3:mini"
    ollama_base_url: str = "http://localhost:11434"
    temperature: float = 0.1
    context_window: int = 2048
    chroma_path: str = "D:/jarvis-agent/agent/data/chroma"
    max_short_term: int = 3
    max_iterations: int = 2
    verbose: bool = False
    # Model used for agentic planning / replanning / reflection.
    # Must be a model that supports Ollama tool-calling
    # (e.g. "llama3.1", "qwen2.5", "mistral-nemo", "firefunction-v2").
    # Leave empty to reuse `model` above.
    agentic_model: str = "phi3:mini"