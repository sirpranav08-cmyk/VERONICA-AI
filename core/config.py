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