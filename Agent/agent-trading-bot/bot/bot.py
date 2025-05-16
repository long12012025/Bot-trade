import time
import logging
from datetime import datetime

class TradingBot:
    def __init__(self, strategy_selector, memory_manager, api_client, trade_symbol, trade_quantity):
        """
        :param strategy_selector: StrategySelector instance để lấy quyết định chiến lược.
        :param memory_manager: MemoryManager instance để lưu lịch sử.
        :param api_client: Client API kết nối sàn (Binance, v.v).
        :param trade_symbol: Chuỗi ký hiệu cặp giao dịch, ví dụ "BTCUSDT".
        :param trade_quantity: Số lượng lệnh mỗi lần đặt.
        """
        self.strategy_selector = strategy_selector
        self.memory = memory_manager
        self.api_client = api_client
        self.symbol = trade_symbol
        self.quantity = trade_quantity
        self.position = None  # "long", "short", None
        self.open_order_id = None

    def get_latest_candle(self, interval="5m"):
        """
        Lấy nến gần nhất từ sàn qua api_client
        """
        candles = self.api_client.get_candles(self.symbol, interval, limit=1)
        if not candles:
            logging.error("Không lấy được dữ liệu nến.")
            return None
        return candles[0]  # Giả sử định dạng dict có các key: open, close, high, low, volume, timestamp

    def get_account_position(self):
        """
        Lấy trạng thái vị thế hiện tại trên sàn (long, short, hoặc không có vị thế)
        """
        position = self.api_client.get_position(self.symbol)
        self.position = position
        return position

    def place_order(self, side):
        """
        Đặt lệnh mua hoặc bán
        :param side: "BUY" hoặc "SELL"
        :return: order_id nếu thành công, None nếu lỗi
        """
        try:
            order = self.api_client.create_order(
                symbol=self.symbol,
                side=side,
                type="MARKET",
                quantity=self.quantity
            )
            order_id = order.get("orderId")
            logging.info(f"Đặt lệnh {side} thành công, order_id={order_id}")
            self.open_order_id = order_id
            return order_id
        except Exception as e:
            logging.error(f"Lỗi đặt lệnh {side}: {e}")
            return None

    def close_position(self):
        """
        Đóng vị thế hiện tại nếu có.
        """
        if self.position is None:
            logging.info("Không có vị thế để đóng.")
            return
        side = "SELL" if self.position == "long" else "BUY"
        order_id = self.place_order(side)
        if order_id:
            logging.info(f"Đóng vị thế {self.position} bằng lệnh {side}.")
            self.position = None
            self.open_order_id = None

    def decide_and_trade(self):
        """
        Lấy dữ liệu nến, quyết định chiến lược, và thực thi lệnh tương ứng.
        """
        candle = self.get_latest_candle()
        if candle is None:
            return

        # Lấy quyết định chiến lược từ StrategySelector (AI hoặc rule cứng)
        base_prompt = "Bạn là chuyên gia trading, dựa vào dữ liệu sau đây, hãy đề xuất hành động: BUY, SELL hoặc HOLD."
        strategy = self.strategy_selector.select_strategy(base_prompt)

        logging.info(f"Chiến lược nhận được: {strategy}")

        # Chuyển chiến lược sang hành động cụ thể
        action = None
        strategy_lower = strategy.strip().lower()
        if "buy" in strategy_lower:
            action = "BUY"
        elif "sell" in strategy_lower:
            action = "SELL"
        else:
            action = "HOLD"

        # Thực hiện hành động
        if action == "BUY":
            if self.position == "long":
                logging.info("Đã có vị thế LONG, không đặt lệnh mua thêm.")
            else:
                # Nếu đang short, đóng short trước rồi mở long
                if self.position == "short":
                    self.close_position()
                self.place_order("BUY")
                self.position = "long"
        elif action == "SELL":
            if self.position == "short":
                logging.info("Đã có vị thế SHORT, không đặt lệnh bán thêm.")
            else:
                # Nếu đang long, đóng long trước rồi mở short
                if self.position == "long":
                    self.close_position()
                self.place_order("SELL")
                self.position = "short"
        else:
            logging.info("Giữ vị thế hiện tại, không thực hiện lệnh.")

        # Lưu lịch sử giao dịch
        self.memory.add_record("trades", {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "strategy": strategy,
            "position": self.position,
            "symbol": self.symbol
        })

    def run(self, interval_seconds=300):
        """
        Chạy bot liên tục, kiểm tra và giao dịch theo chu kỳ.
        """
        logging.info("Bắt đầu chạy bot trading...")
        while True:
            try:
                self.get_account_position()  # Cập nhật trạng thái vị thế hiện tại
                self.decide_and_trade()
            except Exception as e:
                logging.error(f"Lỗi khi chạy bot: {e}")
            time.sleep(interval_seconds)
