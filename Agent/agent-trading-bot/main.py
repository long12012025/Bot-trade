from agent.ai_client import AIClient
from agent.memory_manager import MemoryManager
from agent.strategy_selector import StrategySelector

def main():
    # Khởi tạo các thành phần
    ai_client = AIClient(model="gpt-4", temperature=0.7)
    memory_manager = MemoryManager()
    strategy_selector = StrategySelector(memory_manager, ai_client)

    # Thêm dữ liệu giả lập nếu chưa có (chạy lần đầu)
    if not memory_manager.get_records("strategies"):
        memory_manager.add_record("strategies", {
            "strategy_name": "scalping",
            "result": "win",
            "profit": 12.5
        })
        memory_manager.add_record("strategies", {
            "strategy_name": "swing",
            "result": "loss",
            "profit": -5.2
        })
        memory_manager.add_record("strategies", {
            "strategy_name": "trend_following",
            "result": "win",
            "profit": 8.3
        })

    # Chuẩn bị prompt gốc
    base_prompt = "Đề xuất chiến lược giao dịch tốt nhất dựa trên dữ liệu hiện tại."

    # Lấy chiến lược tốt nhất
    best_strategy = strategy_selector.select_strategy(base_prompt)
    print("📈 Chiến lược được chọn:", best_strategy)

if __name__ == "__main__":
    main()
