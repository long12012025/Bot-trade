import logging
from typing import Callable, Optional, Dict
from data.collector import BinanceFuturesCollector
from data.indicators import Indicators

class LiveFeed:
    def __init__(self, symbol: str, interval: str = "5m"):
        self.symbol = symbol
        self.interval = interval
        self.collector = BinanceFuturesCollector(symbol, interval)
        self.indicators = Indicators()
        self.candles = []  # Lưu nến mới nhất để tính chỉ báo

    def _on_new_candle(self, candle: Dict):
        # Thêm nến mới vào bộ nhớ
        self.candles.append(candle)
        # Giữ lại tối đa 500 nến gần nhất để tính chỉ báo
        if len(self.candles) > 500:
            self.candles.pop(0)

        # Tính các chỉ báo quan trọng (EMA, RSI, MACD...)
        # Chuẩn bị dữ liệu dạng list dict cho Indicators
        closes = [c['close'] for c in self.candles]
        highs = [c['high'] for c in self.candles]
        lows = [c['low'] for c in self.candles]

        feature_vector = {}

        if len(closes) >= 14:
            feature_vector['rsi'] = self.indicators.rsi(closes, 14)[-1]
        if len(closes) >= 26:
            feature_vector['ema_12'] = self.indicators.ema(closes, 12)[-1]
            feature_vector['ema_26'] = self.indicators.ema(closes, 26)[-1]
            macd_line, signal_line = self.indicators.macd(closes)
            feature_vector['macd'] = macd_line[-1]
            feature_vector['macd_signal'] = signal_line[-1]

        # Gọi callback để AI dùng dữ liệu mới (nếu có)
        if self.callback:
            self.callback(feature_vector)

    def start(self, callback: Optional[Callable[[Dict], None]] = None):
        self.callback = callback
        logging.info(f"LiveFeed bắt đầu với symbol {self.symbol} interval {self.interval}")
        self.collector.stream_realtime(self._on_new_candle)

    def stop(self):
        self.collector.stop_stream()
        logging.info("LiveFeed đã dừng.")
