import json
import os
from datetime import datetime

class MemoryManager:
    def __init__(self, memory_file="memory.json"):
        self.memory_file = memory_file
        self.memory = self.load_memory()

    def load_memory(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_memory(self):
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, indent=4, ensure_ascii=False)

    def add_record(self, key: str, value):
        timestamp = datetime.utcnow().isoformat()
        if key not in self.memory:
            self.memory[key] = []
        self.memory[key].append({"timestamp": timestamp, "value": value})
        self.save_memory()

    def get_records(self, key: str, limit: int = 10):
        if key in self.memory:
            return self.memory[key][-limit:]
        return []

    def clear_memory(self):
        self.memory = {}
        self.save_memory()
