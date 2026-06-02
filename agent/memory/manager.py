"""
Memory manager:
- Short-term: sliding window of last N messages
- Long-term: JSON file (persistent across restarts)
- ChromaDB: semantic search (optional)
"""
import json
import os
from collections import deque
from datetime import datetime
from core.config import Config

try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


class MemoryManager:
    def __init__(self, config: Config):
        self.config = config
        self.short_term = deque(maxlen=config.max_short_term)
        self.memory_file = "D:/jarvis-agent/agent/data/memory.json"
        self.facts_file = "D:/jarvis-agent/agent/data/facts.json"
        self.long_term = None

        # Create data directory
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)

        # Load persistent memory
        self.persistent = self._load_json(self.memory_file, [])
        self.facts = self._load_json(self.facts_file, {})

        # Load last N messages into short term
        for msg in self.persistent[-config.max_short_term:]:
            self.short_term.append(msg)

        # ChromaDB
        if CHROMA_AVAILABLE:
            try:
                client = chromadb.PersistentClient(path=config.chroma_path)
                self.long_term = client.get_or_create_collection("jarvis_memory")
                print("[Memory] ChromaDB long-term memory initialized")
            except Exception as e:
                print(f"[Memory] ChromaDB unavailable: {e}")

        print(f"[Memory] Loaded {len(self.persistent)} messages from disk")
        print(f"[Memory] Loaded {len(self.facts)} facts from disk")

    def _load_json(self, path, default):
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[Memory] Load error {path}: {e}")
        return default

    def _save_json(self, path, data):
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Memory] Save error {path}: {e}")

    def add_user(self, content: str):
        msg = {
            "role": "user",
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.short_term.append(msg)
        self.persistent.append(msg)
        # Keep only last 500 messages on disk
        if len(self.persistent) > 500:
            self.persistent = self.persistent[-500:]
        self._save_json(self.memory_file, self.persistent)
        self._extract_facts(content)

    def add_assistant(self, content: str):
        msg = {
            "role": "assistant",
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.short_term.append(msg)
        self.persistent.append(msg)
        if len(self.persistent) > 500:
            self.persistent = self.persistent[-500:]
        self._save_json(self.memory_file, self.persistent)

    def remember_fact(self, key: str, value: str):
        """Store a named fact persistently."""
        self.facts[key] = {
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        self._save_json(self.facts_file, self.facts)
        print(f"[Memory] Fact stored: {key} = {value}")

    def recall_fact(self, key: str) -> str:
        """Recall a named fact."""
        return self.facts.get(key, {}).get("value", None)

    def get_all_facts(self) -> str:
        """Get all facts as a formatted string."""
        if not self.facts:
            return ""
        lines = []
        for k, v in self.facts.items():
            lines.append(f"- {k}: {v['value']}")
        return "\n".join(lines)

    def _extract_facts(self, text: str):
        """Auto-extract facts from user messages."""
        import re
        lower = text.lower()

        # Name
        m = re.search(r'(?:my name is|i am|i\'m|call me)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', text, re.I)
        if m:
            self.remember_fact('user_name', m.group(1).strip())

        # Age
        m = re.search(r'(?:i\'m|i am|my age is)\s+(\d{1,2})\s*(?:years|year|yrs)?\s*(?:old)?', text, re.I)
        if m:
            self.remember_fact('user_age', m.group(1))

        # Location
        m = re.search(r'(?:i live in|i\'m from|i am from|based in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})', text, re.I)
        if m:
            self.remember_fact('user_location', m.group(1).strip())

        # Profession
        m = re.search(r'(?:i work as|i\'m a|i am a|my job is)\s+(.{3,40}?)(?:\.|,|$)', text, re.I)
        if m:
            self.remember_fact('user_profession', m.group(1).strip())

    def get_context(self) -> list:
        """Return sliding window for LLM — without timestamps."""
        return [
            {"role": m["role"], "content": m["content"]}
            for m in self.short_term
        ]

    def get_summary(self) -> str:
        """Get memory summary for system prompt."""
        facts = self.get_all_facts()
        total = len(self.persistent)
        summary = f"Total conversations remembered: {total}\n"
        if facts:
            summary += f"Known facts about user:\n{facts}"
        return summary

    def clear(self):
        self.short_term.clear()

    def clear_all(self):
        """Wipe all memory."""
        self.short_term.clear()
        self.persistent = []
        self.facts = {}
        self._save_json(self.memory_file, [])
        self._save_json(self.facts_file, {})
        print("[Memory] All memory cleared.")