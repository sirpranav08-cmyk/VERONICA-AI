# JARVIS — Local Agent AI Desktop App

**Stack**: Tauri · Python · Ollama · ChromaDB · FastAPI · WebSocket

---

## Architecture

```
┌─────────────────────────────────┐
│   Tauri Desktop Shell (Rust)    │  ← system tray, hotkeys, window
└──────────────┬──────────────────┘
               │ WebSocket ws://127.0.0.1:8765
┌──────────────▼──────────────────┐
│   Python Agent Backend          │
│   ├── core/agent.py             │  ← plan → tool → observe loop
│   ├── core/config.py            │  ← model, memory, limits
│   ├── memory/manager.py         │  ← short-term + ChromaDB
│   └── tools/registry.py        │  ← file, shell, web, OS
└──────────────┬──────────────────┘
               │
      ┌────────▼────────┐
      │  Ollama (local) │  ← Mistral / LLaMA3 / Phi-3
      └─────────────────┘
```

## Quick Start

```bash
# 1. Install Ollama: https://ollama.com/download
# 2. Run setup
bash setup.sh

# 3. Open ui/src/index.html in browser
# OR build Tauri app:
cd .. && cargo tauri dev
```

## Switching Models

Edit `agent/core/config.py`:
```python
model: str = "llama3"   # or "phi3", "gemma2", "codellama"
```

Or pull any model:
```bash
ollama pull llama3
ollama pull phi3
ollama pull codellama
```

## Adding a Custom Tool

In `agent/tools/registry.py`, add to `_register_builtin_tools()`:

```python
@self.register(
    name="my_tool",
    description="Does something useful",
    args_schema={"input": "string"}
)
def my_tool(input: str) -> str:
    return f"Result: {input}"
```

The agent will automatically discover and use it.

## Project Structure

```
jarvis-agent/
├── agent/
│   ├── main.py              # FastAPI + WebSocket server
│   ├── core/
│   │   ├── agent.py         # Agent loop (plan → tool → observe)
│   │   └── config.py        # All settings
│   ├── memory/
│   │   └── manager.py       # Short-term + ChromaDB long-term
│   ├── tools/
│   │   └── registry.py      # Built-in tools
│   └── requirements.txt
├── src-tauri/
│   └── src/main.rs          # Tauri desktop shell
├── ui/
│   └── src/index.html       # Chat UI
├── setup.sh
└── README.md
```

## Built-in Tools

| Tool | Description |
|------|-------------|
| `read_file` | Read any file |
| `write_file` | Write/create files |
| `list_directory` | Browse filesystem |
| `run_shell` | Execute shell commands (blocklist enforced) |
| `web_search` | DuckDuckGo (no API key needed) |
| `system_info` | CPU, RAM, disk stats |
| `recall_memory` | Semantic search in past conversations |

## Roadmap

- [ ] Browser automation (Playwright)
- [ ] Code execution sandbox (Docker)
- [ ] Multi-agent task splitting
- [ ] Scheduled/triggered automation
- [ ] Plugin system for third-party tools
