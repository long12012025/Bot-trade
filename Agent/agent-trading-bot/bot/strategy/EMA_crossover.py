import pandas as pd
from strategy.base_strategy import BaseStrategy

class EmaCrossoverStrategy(BaseStrategy):
    def __init__(self, short_period=12, long_period=26):
        super().__init__()
        self.short_period = short_period
        self.long_period = long_period
        self.data = pd.DataFrame()  # Lưu lịch sử giá để tính EMA
        self.position_open = False
        self.position_type = None  # 'long' hoặc 'short'

    def update_data(self, candle):
        # candle là dict chứa các key: open, high, low, close, volume, timestamp
        new_row = {
            "close": candle["close"],
            "timestamp": candle["timestamp"]
        }
        self.data = pd.concat([self.data, pd.DataFrame([new_row])], ignore_index=True)
        # Giữ data size hợp lý (vd 1000 dòng)
        if len(self.data) > 1000:
            self.data = self.data.iloc[-1000:]
        # Tính EMA
        self.data["ema_short"] = self.data["close"].ewm(span=self.short_period, adjust=False).mean()
        self.data["ema_long"] = self.data["close"].ewm(span=self.long_period, adjust=False).mean()

    def should_open_position(self, candle) -> bool:
        self.update_data(candle)
        if len(self.data) < max(self.short_period, self.long_period):
            return False
        latest = self.data.iloc[-1]
        prev = self.data.iloc[-2]

        # Tín hiệu mua: EMA ngắn cắt lên EMA dài
        if not self.position_open and prev["ema_short"] <= prev["ema_long"] and latest["ema_short"] > latest["ema_long"]:
            self.position_type = "long"
            self.position_open = True
            return True

        # Tín hiệu bán khống: EMA ngắn cắt xuống EMA dài
        if not self.position_open and prev["ema_short"] >= prev["ema_long"] and latest["ema_short"] < latest["ema_long"]:
            self.position_type = "short"
            self.position_open = True
            return True

        return False

    def should_close_position(self, candle) -> bool:
        self.update_data(candle)
        if not self.position_open:
            return False
        latest = self.data.iloc[-1]
        prev = self.data.iloc[-2]

        # Đóng vị thế long khi EMA ngắn cắt xuống EMA dài
        if self.position_type == "long" and prev["ema_short"] >= prev["ema_long"] and latest["ema_short"] < latest["ema_long"]:
            self.position_open = False
            self.position_type = None
            return True

        # Đóng vị thế short khi EMA ngắn cắt lên EMA dài
        if self.position_type == "short" and prev["ema_short"] <= prev["ema_long"] and latest["ema_short"] > latest["ema_long"]:
            self.position_open = False
            self.position_type = None
            return True

        return False

    def get_signal_type(self, candle) -> str:
        return self.position_type
