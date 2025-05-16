import pandas as pd
from strategy.base_strategy import BaseStrategy

class BreakoutStrategy(BaseStrategy):
    def __init__(self, window=20):
        super().__init__()
        self.window = window
        self.data = pd.DataFrame()  # Lưu lịch sử giá để tính đỉnh đáy
        self.position_open = False
        self.position_type = None

    def update_data(self, candle):
        new_row = {
            "high": candle["high"],
            "low": candle["low"],
            "close": candle["close"],
            "timestamp": candle["timestamp"]
        }
        self.data = pd.concat([self.data, pd.DataFrame([new_row])], ignore_index=True)
        if len(self.data) > 1000:
            self.data = self.data.iloc[-1000:]

    def should_open_position(self, candle) -> bool:
        self.update_data(candle)
        if len(self.data) < self.window:
            return False
        highest_high = self.data["high"].iloc[-self.window:].max()
        lowest_low = self.data["low"].iloc[-self.window:].min()

        if not self.position_open:
            # Bứt phá lên trên đỉnh cao nhất window, mở vị thế long
            if candle["close"] > highest_high:
                self.position_open = True
                self.position_type = "long"
                return True
            # Bứt phá xuống dưới đáy thấp nhất window, mở vị thế short
            if candle["close"] < lowest_low:
                self.position_open = True
                self.position_type = "short"
                return True
        return False

    def should_close_position(self, candle) -> bool:
        self.update_data(candle)
        if not self.position_open:
            return False

        # Đóng vị thế long khi giá đóng dưới đáy thấp nhất window
        if self.position_type == "long":
            lowest_low = self.data["low"].iloc[-self.window:].min()
            if candle["close"] < lowest_low:
                self.position_open = False
                self.position_type = None
                return True

        # Đóng vị thế short khi giá đóng trên đỉnh cao nhất window
        if self.position_type == "short":
            highest_high = self.data["high"].iloc[-self.window:].max()
            if candle["close"] > highest_high:
                self.position_open = False
                self.position_type = None
                return True

        return False

    def get_signal_type(self, candle) -> str:
        return self.position_type
