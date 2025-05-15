class TradingAgent:
    def __init__(self, memory_manager, data_interface, strategy_selector, ai_client):
        self.memory = memory_manager
        self.data_interface = data_interface
        self.strategy_selector = strategy_selector
        self.ai_client = ai_client
        self.current_strategy = None

    def analyze_market(self):
        market_data = self.data_interface.get_latest_data()
        return market_data

    def decide_strategy(self, market_data):
        # Gửi dữ liệu và trạng thái hiện tại đến AI để lấy đề xuất chiến lược
        prompt = self._build_prompt(market_data)
        strategy = self.ai_client.get_strategy(prompt)
        self.current_strategy = strategy
        self.memory.save_strategy(strategy)
        return strategy

    def _build_prompt(self, market_data):
        # Xây prompt dựa trên dữ liệu thị trường và trạng thái trước đó
        prompt = f"Market data: {market_data}\n"
        prompt += f"Previous strategies: {self.memory.get_strategy_history()}\n"
        prompt += "Suggest the best trading strategy:"
        return prompt

    def run(self):
        market_data = self.analyze_market()
        strategy = self.decide_strategy(market_data)
        return strategy
