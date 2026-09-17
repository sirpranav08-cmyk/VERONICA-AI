code = open(r"D:\jarvis-agent\agent\tools\registry.py").read()

# Find the last properly indented tool and add after it
addition = '''
        @self.register(
            name="agi_status",
            description="Show VERONICA AGI status",
            args_schema={}
        )
        def agi_status() -> str:
            try:
                import veronica_agi
                agi = veronica_agi.get_instance()
                if agi: return agi.get_status()
                return "AGI not initialized, Sir."
            except Exception as e:
                return f"AGI error: {e}"

        @self.register(
            name="agi_remember",
            description="Store something in AGI infinite memory",
            args_schema={"content": "what to remember"}
        )
        def agi_remember(content: str, importance: float = 0.7) -> str:
            try:
                import veronica_agi
                agi = veronica_agi.get_instance()
                if agi:
                    node_id = agi.memory.store(content, "user_fact", importance)
                    return f"Stored in AGI memory, Sir. ID: {node_id}"
                return "AGI not ready, Sir."
            except Exception as e:
                return f"Memory error: {e}"

        @self.register(
            name="agi_recall",
            description="Recall memories from AGI",
            args_schema={"query": "what to recall"}
        )
        def agi_recall(query: str) -> str:
            try:
                import veronica_agi
                agi = veronica_agi.get_instance()
                if agi:
                    memories = agi.memory.recall(query, top_k=5)
                    if not memories:
                        return "No relevant memories found, Sir."
                    lines = [f"Recalled {len(memories)} memories, Sir:"]
                    for m in memories:
                        lines.append(f"• {m['content'][:80]}")
                    return "\\n".join(lines)
                return "AGI not ready, Sir."
            except Exception as e:
                return f"Recall error: {e}"

        @self.register(
            name="agi_introspect",
            description="VERONICA reflects on her own thinking",
            args_schema={}
        )
        def agi_introspect() -> str:
            try:
                import veronica_agi
                agi = veronica_agi.get_instance()
                if agi: return agi.meta.introspect()
                return "AGI not ready, Sir."
            except Exception as e:
                return f"Introspect error: {e}"

        @self.register(
            name="agi_code_health",
            description="Check health of VERONICA code",
            args_schema={}
        )
        def agi_code_health() -> str:
            try:
                import veronica_agi
                agi = veronica_agi.get_instance()
                if agi: return agi.improve.get_health_report()
                return "AGI not ready, Sir."
            except Exception as e:
                return f"Health error: {e}"
'''

# Remove broken tools at end and add clean ones
# Find last good closing of _register_builtin_tools
lines = code.split('\\n')
clean_lines = []
skip = False
for line in lines:
    if 'def agi_status' in line or 'def agi_remember' in line or \
       'def agi_recall' in line or 'def agi_introspect' in line or \
       'def agi_code_health' in line or \
       ('def read_file' in line and '@self.register' not in lines[max(0,lines.index(line)-3):lines.index(line)]):
        skip = False
    if '@self.register' in line and 'agi_' in ''.join(lines[lines.index(line):lines.index(line)+3]):
        skip = True
    if not skip:
        clean_lines.append(line)

new_code = '\\n'.join(clean_lines)
new_code = new_code.rstrip() + '\\n' + addition

open(r"D:\jarvis-agent\agent\tools\registry.py", 'w').write(new_code)
print("Done!")