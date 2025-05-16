import logging

class StrategySelector:
    base_prompt = "Bạn là chuyên gia trading thông minh. Phân tích lịch sử giao dịch và hiệu quả trước đây, đề xuất chiến lược trading cụ thể, tối ưu lợi nhuận và giảm thiểu rủi ro, dễ áp dụng thực tế."
    best_strategy = strategy_selector.select_strategy(base_prompt)

    def __init__(self, memory_manager, ai_client):
        """
        Khởi tạo StrategySelector với memory_manager và ai_client đã có.
        """
        self.memory = memory_manager
        self.ai = ai_client

    def analyze_history(self, limit=10):
        """
        Phân tích lịch sử chiến lược gần đây để tổng hợp số lần thắng, thua và lợi nhuận trung bình.
        Trả về dict hoặc None nếu không có dữ liệu.
        """
        records = self.memory.get_records("strategies", limit=limit)
        if not records:
            logging.info("Không có lịch sử chiến lược để phân tích.")
            return None

        wins = 0
        losses = 0
        total_profit = 0
        count_profit_records = 0

        for record in records:
            result = record.get("result")
            profit = record.get("profit")
            if result:
                if result.lower() == "win":
                    wins += 1
                elif result.lower() == "loss":
                    losses += 1
            if profit is not None:
                try:
                    total_profit += float(profit)
                    count_profit_records += 1
                except Exception as e:
                    logging.warning(f"Lỗi khi phân tích lợi nhuận: {e}")

        avg_profit = total_profit / count_profit_records if count_profit_records > 0 else 0

        summary = {
            "wins": wins,
            "losses": losses,
            "avg_profit": avg_profit,
            "total": len(records)
        }
        logging.info(f"Phân tích lịch sử: {summary}")
        return summary

    def build_prompt(self, base_prompt, history_summary):
        """
        Tạo prompt gửi cho AI dựa trên prompt gốc và tóm tắt lịch sử.
        """
        if history_summary is None:
            return base_prompt

        if history_summary["losses"] > history_summary["wins"]:
            enhanced_prompt = (base_prompt +
                               "\nLưu ý: Các chiến lược trước đây có tỉ lệ thua cao, "
                               "vui lòng đề xuất chiến lược mới cải thiện hiệu quả và giảm rủi ro.")
        elif history_summary["avg_profit"] < 0.01:
            enhanced_prompt = (base_prompt +
                               "\nLưu ý: Lợi nhuận trung bình thấp, hãy đề xuất chiến lược tối ưu hơn.")
        else:
            enhanced_prompt = base_prompt + "\nVui lòng đưa ra chiến lược tốt nhất dựa trên dữ liệu hiện tại."

        logging.info(f"Prompt gửi AI: {enhanced_prompt}")
        return enhanced_prompt

    def select_strategy(self, base_prompt: str):
        """
        Lấy chiến lược từ AI dựa trên prompt đã được điều chỉnh theo lịch sử.
        """
        history_summary = self.analyze_history(limit=10)
        prompt = self.build_prompt(base_prompt, history_summary)
        try:
            strategy = self.ai.get_strategy(prompt)
        except Exception as e:
            logging.error(f"Lỗi khi gọi AI để lấy chiến lược: {e}")
            strategy = "Không thể lấy chiến lược do lỗi hệ thống."
        return strategy
