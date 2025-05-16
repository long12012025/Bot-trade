import time
import logging
from datetime import datetime

from core.exchange_api import ExchangeAPI
from core.position_manager import PositionManager
from core.order_executor import OrderExecutor
from core.risk_manager import RiskManager
from model.predictor import Predictor
from strategy.base_strategy import StrategySelector  # Có thể là AI hoặc rules
from memory_manager import MemoryManager  # Nơi bạn lưu giao dịch (pickle, JSON, DB)

class TradingBot:
    def __init__(self, config):
        """
        :param config: Dict chứa config cơ bản như symbol, quantity, leverage...
        """
        self.symbol = config["symbol"]
        self.quantity = config["quantity"]
        self.interval = config.get("interval", "5m")

        # Khởi tạo các thành phần
        self.api = ExchangeAPI(config)
        self.memory = MemoryManager()
        self.executor = OrderExecutor(self.api)
        self.position_manager = PositionManager(self.api, self.executor)
        self.risk_manager = RiskManager()
        self.strategy_selector = StrategySelector()
        self.model_predictor = Predictor()
        
        self.current_position = None

    def get_market_snapshot(self):
        candles = self.api.get_candles(self.symbol, self.interval, limit=50)
        if not candles:
            logging.warning("Không lấy được dữ liệu nến.")
            return None
        indicators = self.api.compute_indicators(candles)  # Nếu có indicators.py
        return {
            "candles": candles,
            "indicators": indicators
        }

    def decide_action(self, market_snapshot):
        """
        Trả về hành động dựa trên AI hoặc chiến lược.
        """
        # Lấy dự đoán từ mô hình AI
        ai_action = self.model_predictor.predict(market_snapshot)
        base_prompt = f"Dựa trên dữ liệu hiện tại: {market_snapshot}, mô hình gợi ý {ai_action}."

        # Chiến lược chọn giữa AI và rule
        strategy = self.strategy_selector.select_strategy(base_prompt, ai_action, market_snapshot)
        strategy_lower = strategy.strip().lower()
        
        if "buy" in strategy_lower:
            return "BUY"
        elif "sell" in strategy_lower:
            return "SELL"
        else:
            return "HOLD"

    def evaluate_risk(self, market_snapshot, action):
        """
        Kiểm tra risk/reward trước khi cho phép hành động
        """
        rr_ok = self.risk_manager.evaluate(
            market_snapshot=market_snapshot,
            action=action,
            current_position=self.current_position,
            symbol=self.symbol
        )
        if not rr_ok:
            logging.info(f"Hành động {action} bị chặn bởi Risk Manager do RR không đạt.")
            return False
        return True

    def execute_trade(self, action):
        """
        Thực hiện giao dịch thực tế dựa vào hành động đã quyết định
        """
        if action == "BUY":
            if self.current_position == "long":
                logging.info("Đã có lệnh long, bỏ qua.")
                return
            if self.current_position == "short":
                self.position_manager.close_position(self.symbol)
            self.position_manager.open_long(self.symbol, self.quantity)
            self.current_position = "long"

        elif action == "SELL":
            if self.current_position == "short":
                logging.info("Đã có lệnh short, bỏ qua.")
                return
            if self.current_position == "long":
                self.position_manager.close_position(self.symbol)
            self.position_manager.open_short(self.symbol, self.quantity)
            self.current_position = "short"

        elif action == "HOLD":
            logging.info("HOLD: Không vào lệnh.")

    def save_trade_log(self, action, strategy, snapshot):
        """
        Lưu thông tin giao dịch để training lại AI hoặc theo dõi hiệu suất.
        """
        self.memory.add_record("trades", {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "strategy": strategy,
            "position": self.current_position,
            "symbol": self.symbol,
            "snapshot": snapshot
        })

    def run(self, interval_seconds=300):
        """
        Chạy bot theo chu kỳ liên tục.
        """
        logging.info("Bot bắt đầu chạy...")
        while True:
            try:
                self.current_position = self.api.get_position(self.symbol)
                snapshot = self.get_market_snapshot()
                if not snapshot:
                    continue

                action = self.decide_action(snapshot)
                logging.info(f"Chiến lược gợi ý: {action}")

                if action != "HOLD" and self.evaluate_risk(snapshot, action):
                    self.execute_trade(action)

                self.save_trade_log(action, action, snapshot)

            except Exception as e:
                logging.error(f"Lỗi trong vòng lặp bot: {e}")

            time.sleep(interval_seconds)
