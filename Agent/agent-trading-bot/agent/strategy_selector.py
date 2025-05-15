from typing import List, Dict, Optional
from agent.ai_client import AIClient

class StrategySelector:
    def __init__(self, memory_manager, ai_client: AIClient):
        self.memory = memory_manager
        self.ai_client = ai_client
        self.available_strategies = [
            {"name": "scalping", "description": "Giao dịch nhanh trong thời gian rất ngắn"},
            {"name": "swing", "description": "Giữ lệnh vài ngày, tận dụng dao động trung hạn"},
            {"name": "trend_following", "description": "Theo xu hướng thị trường dài hạn"},
        ]

    def evaluate_strategy_performance(self, history: List[Dict]) -> Dict[str, float]:
        performance = {}
        counts = {}

        for record in history:
            strat = record.get("strategy_name")
            profit = record.get("profit", 0)
            if strat not in performance:
                performance[strat] = 0
                counts[strat] = 0
            performance[strat] += profit
            counts[strat] += 1

        for strat in performance:
            performance[strat] /= counts[strat]

        return performance

    def get_ai_advice(self, history: List[Dict]) -> Optional[str]:
        prompt = "Bạn là chuyên gia phân tích giao dịch crypto. Dựa vào dữ liệu lịch sử sau, đề xuất chiến lược giao dịch tốt nhất trong danh sách:\n"
        prompt += "Chiến lược: scalping, swing, trend_following\n"
        prompt += "Dữ liệu lịch sử:\n"
        for record in history[-10:]:
            prompt += f"- {record}\n"
        prompt += "Hãy trả về duy nhất tên chiến lược phù hợp nhất."

        response = self.ai_client.get_strategy(prompt)
        if response:
            # Làm sạch kết quả và so khớp với chiến lược có sẵn
            cleaned = response.lower().strip()
            for strat in self.available_strategies:
                if strat["name"] in cleaned:
                    return strat["name"]
        return None

    def select_best_strategy(self) -> Optional[Dict]:
        history = self.memory.get_records("strategies", limit=100)
        if not history:
            return self.available_strategies[0]

        performance = self.evaluate_strategy_performance(history)
        ai_suggestion = self.get_ai_advice(history)

        if ai_suggestion:
            for strat in self.available_strategies:
                if strat["name"] == ai_suggestion:
                    return strat

        if performance:
            best_strategy_name = max(performance, key=performance.get)
            for strat in self.available_strategies:
                if strat["name"] == best_strategy_name:
                    return strat

        return self.available_strategies[0]
