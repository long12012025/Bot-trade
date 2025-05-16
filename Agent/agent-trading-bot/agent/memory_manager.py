import json
import os
import time  # cần import time để dùng time.time()

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

    def add_record(self, category: str, data: dict):
        if category not in self.memory:
            self.memory[category] = []
        record = data.copy()
        record["timestamp"] = time.time()
        self.memory[category].append(record)
        self.save_memory()  # lưu lại mỗi lần thêm record

    def get_records(self, category: str, limit=10):
        if category not in self.memory:
            return []
        return self.memory[category][-limit:]

    def clear_memory(self):
        self.memory = {}
        self.save_memory()
