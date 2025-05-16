import time
import logging
import requests
import json
from datetime import datetime
from typing import List, Dict, Optional, Callable
from threading import Thread
from websocket import WebSocketApp
import pandas as pd

from data.indicators import calculate_all_indicators


class BinanceFuturesCollector:
    REST_URL = "https://fapi.binance.com"
    WS_BASE_URL = "wss://fstream.binance.com"

    def __init__(self, symbol: str, interval: str = "5m"):
        self.symbol = symbol.upper()
        self.interval = interval
        self.ws_app: Optional[WebSocketApp] = None
        self.ws_thread: Optional[Thread] = None
        self.logger = logging.getLogger(f"BinanceFuturesCollector:{self.symbol}")
        self.reconnect = True  # Cho phép tự động reconnect WebSocket

    # ========== REST METHODS ==========

    def get_historical_dataframe(
        self,
        limit: int = 1000,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        with_indicators: bool = True
    ) -> pd.DataFrame:
        candles = self.get_historical_candles(limit, start_time, end_time)
        if not candles:
            return pd.DataFrame()
        df = self._to_dataframe(candles)
        return calculate_all_indicators(df) if with_indicators else df

    def get_historical_candles(
        self,
        limit: int = 1000,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[Dict]:
        url = f"{self.REST_URL}/fapi/v1/klines"
        params = {
            "symbol": self.symbol,
            "interval": self.interval,
            "limit": limit
        }
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            raw_candles = response.json()
            return self._parse_klines(raw_candles)
        except Exception as e:
            self.logger.error(f"[REST] Lỗi lấy dữ liệu nến: {e}")
            return []

    def get_latest_candle(self) -> Optional[Dict]:
        candles = self.get_historical_candles(limit=1)
        return candles[0] if candles else None

    def _parse_klines(self, raw_klines: List) -> List[Dict]:
        return [{
            "timestamp": item[0],
            "open_time": datetime.utcfromtimestamp(item[0] / 1000),
            "open": float(item[1]),
            "high": float(item[2]),
            "low": float(item[3]),
            "close": float(item[4]),
            "volume": float(item[5]),
            "close_time": datetime.utcfromtimestamp(item[6] / 1000)
        } for item in raw_klines]

    def _to_dataframe(self, candles: List[Dict]) -> pd.DataFrame:
        df = pd.DataFrame(candles)
        df["open_time"] = pd.to_datetime(df["open_time"])
        df.set_index("open_time", inplace=True)
        return df

    # ========== WEBSOCKET METHODS ==========

    def stream_realtime(self, on_candle_callback: Callable[[Dict], None]):
        """
        Stream dữ liệu real-time qua WebSocket. Gọi callback mỗi khi có nến mới.
        """
        def on_message(ws, message):
            try:
                msg = json.loads(message)
                if "k" in msg:
                    k = msg["k"]
                    if k["x"]:  # Nến đã đóng
                        candle = {
                            "timestamp": k["t"],
                            "open_time": datetime.utcfromtimestamp(k["t"] / 1000),
                            "open": float(k["o"]),
                            "high": float(k["h"]),
                            "low": float(k["l"]),
                            "close": float(k["c"]),
                            "volume": float(k["v"]),
                            "close_time": datetime.utcfromtimestamp(k["T"] / 1000)
                        }
                        on_candle_callback(candle)
            except Exception as e:
                self.logger.error(f"[WebSocket] Lỗi xử lý message: {e}")

        def on_error(ws, error):
            self.logger.error(f"[WebSocket] Lỗi: {error}")

        def on_close(ws, close_status_code, close_msg):
            self.logger.warning(f"[WebSocket] Kết nối đóng: {close_status_code} - {close_msg}")
            if self.reconnect:
                self.logger.info("[WebSocket] Đang thử kết nối lại sau 5 giây...")
                time.sleep(5)
                self._start_ws(on_candle_callback)

        def on_open(ws):
            self.logger.info("[WebSocket] Kết nối thành công.")

        self._start_ws(on_candle_callback, on_message, on_error, on_close, on_open)

    def _start_ws(self, on_candle_callback, on_message=None, on_error=None, on_close=None, on_open=None):
        stream_name = f"{self.symbol.lower()}@kline_{self.interval}"
        ws_url = f"{self.WS_BASE_URL}/ws/{stream_name}"

        self.ws_app = WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )
        self.ws_thread = Thread(target=self.ws_app.run_forever, daemon=True)
        self.ws_thread.start()
        self.logger.info(f"[WebSocket] Đang stream {self.symbol} - {self.interval}...")

    def stop_stream(self):
        """
        Ngắt kết nối WebSocket.
        """
        self.reconnect = False
        if self.ws_app:
            self.ws_app.close()
            self.logger.info("[WebSocket] Dừng kết nối WebSocket.")
