# Run this to fix registry.py
with open(r"D:\jarvis-agent\agent\tools\registry.py", "a") as f:
    f.write('''
        @self.register(
            name="rational_state",
            description="Show rational agent current state and decisions",
            args_schema={}
        )
        def rational_state() -> str:
            try:
                import rational_agent
                instance = rational_agent.get_instance()
                if instance:
                    instance.perceive()
                    return instance.get_state_summary()
                return "Rational agent not running, Sir."
            except Exception as e:
                return f"Rational agent error: {e}"
''')
print("Fixed!")