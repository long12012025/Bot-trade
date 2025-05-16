import logging
from typing import Dict, Optional, Any
from core.exchange_api import BinanceAPI

class PositionManager:
    def __init__(self, api: BinanceAPI, symbol: str):
        """
        Quản lý vị thế của 1 symbol trên Binance Futures.
        
        Args:
            api: instance BinanceAPI để gọi API.
            symbol: cặp giao dịch, ví dụ "BTCUSDT".
        """
        self.api = api
        self.symbol = symbol.upper()
        self.position: Optional[Dict[str, Any]] = None  # Lưu trạng thái vị thế hiện tại
        self.update_position()

    def update_position(self):
        """Lấy thông tin vị thế hiện tại từ sàn và cập nhật nội bộ."""
        try:
            pos = self.api.get_position(self.symbol)
            if pos:
                self.position = pos
                logging.info(f"[PositionManager] Cập nhật vị thế: {pos}")
            else:
                self.position = None
                logging.info(f"[PositionManager] Không có vị thế mở cho {self.symbol}")
        except Exception as e:
            logging.error(f"[PositionManager] Lỗi khi lấy vị thế {self.symbol}: {e}")
            self.position = None

    def get_position_amount(self) -> float:
        """Trả về số lượng vị thế hiện tại (dương nếu long, âm nếu short)."""
        if self.position:
            amt = float(self.position.get('positionAmt', 0))
            return amt
        return 0.0

    def get_entry_price(self) -> float:
        """Lấy giá vào vị thế hiện tại."""
        if self.position:
            return float(self.position.get('entryPrice', 0))
        return 0.0

    def get_unrealized_pnl(self) -> float:
        """Lấy PNL chưa thực hiện hiện tại."""
        if self.position:
            return float(self.position.get('unRealizedProfit', 0))
        return 0.0

    def get_leverage(self) -> int:
        """Lấy đòn bẩy hiện tại."""
        try:
            lev = self.api.get_leverage(self.symbol)
            return lev
        except Exception as e:
            logging.error(f"[PositionManager] Lỗi lấy leverage: {e}")
            return 1

    def set_leverage(self, leverage: int):
        """Đặt đòn bẩy cho symbol."""
        try:
            self.api.set_leverage(self.symbol, leverage)
            logging.info(f"[PositionManager] Đã đặt leverage={leverage} cho {self.symbol}")
        except Exception as e:
            logging.error(f"[PositionManager] Lỗi đặt leverage: {e}")

    def get_margin_type(self) -> str:
        """Lấy loại margin (cross/isolate)."""
        if self.position:
            return self.position.get('marginType', 'unknown')
        return 'unknown'

    def change_margin_type(self, margin_type: str):
        """Thay đổi margin type: 'CROSSED' hoặc 'ISOLATED'."""
        try:
            self.api.change_margin_type(self.symbol, margin_type)
            logging.info(f"[PositionManager] Đã đổi margin type thành {margin_type} cho {self.symbol}")
        except Exception as e:
            logging.error(f"[PositionManager] Lỗi đổi margin type: {e}")

    def is_position_open(self) -> bool:
        """Kiểm tra xem có vị thế mở hay không."""
        return self.get_position_amount() != 0.0

    def close_position(self):
        """Đóng vị thế hiện tại bằng lệnh thị trường ngược lại."""
        qty = abs(self.get_position_amount())
        if qty == 0:
            logging.info(f"[PositionManager] Không có vị thế mở để đóng cho {self.symbol}")
            return None

        side = 'SELL' if self.get_position_amount() > 0 else 'BUY'

        try:
            order = self.api.place_order(
                symbol=self.symbol,
                side=side,
                order_type='MARKET',
                quantity=qty,
                reduce_only=True
            )
            logging.info(f"[PositionManager] Đã gửi lệnh đóng vị thế: {order}")
            return order
        except Exception as e:
            logging.error(f"[PositionManager] Lỗi khi đóng vị thế: {e}")
            return None

    def monitor_risk(self, pnl_threshold: float = -100.0, margin_ratio_threshold: float = 0.1):
        """
        Giám sát rủi ro vị thế:
        - Cảnh báo nếu lỗ vượt ngưỡng pnl_threshold.
        - Cảnh báo nếu margin ratio thấp hơn margin_ratio_threshold (ví dụ 10%).
        """
        unrealized_pnl = self.get_unrealized_pnl()
        margin_ratio = self.position.get('isolatedMargin') / self.position.get('maintMargin') if self.position else None

        if unrealized_pnl < pnl_threshold:
            logging.warning(f"[PositionManager][RISK] PNL thấp hơn ngưỡng: {unrealized_pnl} < {pnl_threshold}")

        if margin_ratio is not None and margin_ratio < margin_ratio_threshold:
            logging.warning(f"[PositionManager][RISK] Margin ratio thấp: {margin_ratio:.2f} < {margin_ratio_threshold}")

    # Các hàm mở rộng, ví dụ tính toán liquidation price, margin used có thể thêm theo yêu cầu.
