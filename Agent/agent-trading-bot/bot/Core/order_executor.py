import logging
import time
import math
from core.exchange_api import BinanceAPI
from binance.enums import ORDER_TYPE_MARKET, ORDER_TYPE_LIMIT, SIDE_BUY, SIDE_SELL, TIME_IN_FORCE_GTC

class OrderExecutor:
    RETRY_WAIT = 1.0  # Thời gian chờ giữa các lần thử đặt lệnh

    def __init__(self, api: BinanceAPI, max_retries: int = 3, retry_delay: float = RETRY_WAIT):
        """
        Args:
            api: instance BinanceAPI để gọi API thực tế.
            max_retries: số lần thử lại khi đặt lệnh thất bại.
            retry_delay: thời gian chờ giữa các lần thử lại.
        """
        self.api = api
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.symbol_info_cache = {}

    def _get_symbol_info(self, symbol: str):
        """Lấy thông tin chi tiết về symbol (cache để tránh gọi API quá nhiều)."""
        if symbol not in self.symbol_info_cache:
            try:
                info = self.api.client.get_symbol_info(symbol)
                if info is None:
                    logging.error(f"[OrderExecutor] Không lấy được info cho symbol: {symbol}")
                    return None
                self.symbol_info_cache[symbol] = info
                logging.debug(f"[OrderExecutor] Cache info cho symbol: {symbol}")
            except Exception as e:
                logging.error(f"[OrderExecutor] Lỗi lấy symbol info cho {symbol}: {e}")
                return None
        return self.symbol_info_cache[symbol]

    def _round_quantity(self, symbol: str, quantity: float):
        """
        Làm tròn quantity theo stepSize của symbol.
        Tránh lỗi khi đặt lệnh do không đúng bước size quy định.
        """
        info = self._get_symbol_info(symbol)
        if not info or quantity <= 0:
            return quantity
        for f in info['filters']:
            if f['filterType'] == 'LOT_SIZE':
                step_size = float(f['stepSize'])
                precision = max(0, int(round(-math.log(step_size, 10))))
                rounded_qty = math.floor(quantity / step_size) * step_size
                return round(rounded_qty, precision)
        return quantity

    def _round_price(self, symbol: str, price: float):
        """
        Làm tròn giá theo tickSize của symbol.
        Tránh lỗi đặt lệnh giá không hợp lệ.
        """
        info = self._get_symbol_info(symbol)
        if not info or price <= 0:
            return price
        for f in info['filters']:
            if f['filterType'] == 'PRICE_FILTER':
                tick_size = float(f['tickSize'])
                precision = max(0, int(round(-math.log(tick_size, 10))))
                rounded_price = math.floor(price / tick_size) * tick_size
                return round(rounded_price, precision)
        return price

    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = ORDER_TYPE_MARKET,
        price: float = None,
        reduce_only: bool = False,
        timeout: float = 10.0
    ):
        """
        Đặt lệnh mua/bán trên Binance Futures.
        Với limit order, chờ tối đa `timeout` giây rồi tự động hủy nếu không khớp.

        Args:
            symbol: cặp giao dịch (ví dụ "BTCUSDT").
            side: SIDE_BUY hoặc SIDE_SELL.
            quantity: khối lượng lệnh (đã được làm tròn).
            order_type: loại lệnh (market hoặc limit).
            price: giá đặt nếu là limit order.
            reduce_only: True nếu là lệnh giảm vị thế.
            timeout: thời gian chờ lệnh limit khớp trước khi hủy.

        Returns:
            dict order info nếu thành công, None nếu thất bại.
        """
        if quantity <= 0:
            logging.error(f"[OrderExecutor] Quantity phải > 0, nhận: {quantity}")
            return None
        if order_type == ORDER_TYPE_LIMIT and (price is None or price <= 0):
            logging.error(f"[OrderExecutor] Giá phải hợp lệ cho lệnh LIMIT, nhận: {price}")
            return None

        quantity = self._round_quantity(symbol, quantity)
        if price is not None:
            price = self._round_price(symbol, price)

        attempt = 0
        start_time = time.time()

        while attempt < self.max_retries:
            try:
                order = self.api.place_order(
                    symbol=symbol,
                    side=side,
                    order_type=order_type,
                    quantity=quantity,
                    price=price,
                    reduce_only=reduce_only
                )
                if order:
                    logging.info(f"[OrderExecutor] Đặt lệnh thành công: {order}")

                    if order_type == ORDER_TYPE_LIMIT and timeout > 0:
                        order_id = order.get('orderId')
                        if order_id is None:
                            logging.warning(f"[OrderExecutor] Không có orderId trả về, không chờ lệnh khớp.")
                            return order

                        while True:
                            status = self.api.get_order_status(symbol, order_id)
                            if status in ['FILLED', 'CANCELED', 'REJECTED', 'EXPIRED']:
                                logging.info(f"[OrderExecutor] Lệnh {order_id} trạng thái {status}, kết thúc chờ.")
                                break
                            elapsed = time.time() - start_time
                            if elapsed > timeout:
                                self.api.cancel_order(symbol, order_id)
                                logging.info(f"[OrderExecutor] Hủy lệnh {order_id} do timeout {timeout}s.")
                                break
                            time.sleep(0.5)
                    return order
                else:
                    logging.error("[OrderExecutor] Đặt lệnh thất bại, API trả về None.")
                    return None

            except Exception as e:
                logging.warning(f"[OrderExecutor] Lỗi khi đặt lệnh (lần {attempt+1}): {e}")

            attempt += 1
            logging.info(f"[OrderExecutor] Thử lại lần {attempt+1} đặt lệnh sau {self.retry_delay}s...")
            time.sleep(self.retry_delay)

        logging.error(f"[OrderExecutor] Đặt lệnh thất bại sau {self.max_retries} lần thử.")
        return None

    def cancel_order(self, symbol: str, order_id: int):
        """
        Hủy lệnh theo symbol và order_id.
        Trả về kết quả hủy hoặc None nếu lỗi.
        """
        if not symbol or order_id <= 0:
            logging.error(f"[OrderExecutor] cancel_order: symbol hoặc order_id không hợp lệ.")
            return None
        try:
            result = self.api.cancel_order(symbol=symbol, order_id=order_id)
            logging.info(f"[OrderExecutor] Hủy lệnh {order_id} thành công.")
            return result
        except Exception as e:
            logging.error(f"[OrderExecutor] Lỗi khi hủy lệnh {order_id}: {e}")
            return None

    def check_order_status(self, symbol: str, order_id: int):
        """
        Lấy trạng thái lệnh từ Binance.
        Trả về string trạng thái hoặc None nếu lỗi.
        """
        if not symbol or order_id <= 0:
            logging.error(f"[OrderExecutor] check_order_status: symbol hoặc order_id không hợp lệ.")
            return None
        try:
            status = self.api.get_order_status(symbol, order_id)
            logging.info(f"[OrderExecutor] Trạng thái lệnh {order_id}: {status}")
            return status
        except Exception as e:
            logging.error(f"[OrderExecutor] Lỗi lấy trạng thái lệnh {order_id}: {e}")
            return None
