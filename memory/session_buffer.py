class SessionBuffer:
    def __init__(self, max_pairs: int = 5):
        self.history = []
        self.max_pairs = max_pairs
        self.persistent_context = ""

    def set_persistent_context(self, context: str):
        self.persistent_context = context

    def requires_safety_check(self) -> bool:
        context = self.persistent_context.lower()
        return "allergy" in context or "allergic" in context

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        if len(self.history) > self.max_pairs * 2:
            self.history = self.history[-(self.max_pairs * 2):]

    def get_history_string(self) -> str:
        header = f"USER PROFILE: {self.persistent_context}\n" if self.persistent_context else ""
        lines = [
            f"{'Customer' if m['role'] == 'user' else 'Concierge'}: {m['content']}"
            for m in self.history
        ]
        return header + "\n".join(lines)

    def clear(self):
        self.history = []