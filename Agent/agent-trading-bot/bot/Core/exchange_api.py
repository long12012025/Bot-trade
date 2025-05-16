import requests
import time
import hmac
import hashlib
from urllib.parse import urlencode
import logging

class BinanceAPI:
    BASE_URL = "https://fapi.binance.com"

    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret

    def _get_timestamp(self):
        return int(time.time() * 1000)

    def _sign(self, params: dict) -> str:
        query_string = urlencode(params)
        return hmac.new(self.api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

    def _request(self, method: str, path: str, params: dict = None, signed: bool = False):
        if params is None:
            params = {}

        headers = {"X-MBX-APIKEY": self.api_key}
        if signed:
            params['timestamp'] = self._get_timestamp()
            params['signature'] = self._sign(params)

        url = self.BASE_URL + path
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=5)
            elif method == "POST":
                response = requests.post(url, headers=headers, params=params, timeout=5)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Binance API request error: {e}")
            return None

    # === Futures Account / Position ===

    def get_position(self, symbol: str):
        """Lấy thông tin vị thế hiện tại của symbol"""
        path = "/fapi/v2/positionRisk"
        params = {"symbol": symbol}
        return self._request("GET", path, params=params, signed=True)

    def get_account_info(self):
        """Lấy thông tin tài khoản futures"""
        path = "/fapi/v2/account"
        return self._request("GET", path, signed=True)

    def get_leverage(self, symbol: str):
        """Lấy thông tin đòn bẩy hiện tại của symbol"""
        # Binance Futures không có API get leverage trực tiếp, phải lấy từ position
        positions = self.get_position(symbol)
        if positions:
            for pos in positions:
                if pos['symbol'] == symbol:
                    return int(pos.get('leverage', 1))
        return None

    def set_leverage(self, symbol: str, leverage: int):
        """Đặt đòn bẩy cho symbol"""
        path = "/fapi/v1/leverage"
        params = {"symbol": symbol, "leverage": leverage}
        return self._request("POST", path, params=params, signed=True)

    def change_margin_type(self, symbol: str, margin_type: str):
        """
        Thay đổi margin type (CROSSED hoặc ISOLATED)
        """
        path = "/fapi/v1/marginType"
        params = {"symbol": symbol, "marginType": margin_type}
        return self._request("POST", path, params=params, signed=True)

    def place_order(self, symbol: str, side: str, order_type: str, quantity: float, price: float = None,
                    reduce_only: bool = False, time_in_force: str = None):
        """
        Đặt lệnh futures
        side: BUY hoặc SELL
        order_type: LIMIT, MARKET, STOP_MARKET, TAKE_PROFIT_MARKET,...
        """
        path = "/fapi/v1/order"
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
            "reduceOnly": str(reduce_only).lower(),
        }
        if price is not None:
            params["price"] = price
        if time_in_force is not None:
            params["timeInForce"] = time_in_force

        return self._request("POST", path, params=params, signed=True)

    # === Mở rộng tính toán ===

    def calculate_liquidation_price(self, symbol: str):
        """
        Tính toán giá thanh lý từ dữ liệu vị thế.
        Giá trị lấy từ API position, hoặc tính toán thủ công theo công thức Binance.
        """
        pos_list = self.get_position(symbol)
        if not pos_list:
            return None

        for pos in pos_list:
            if pos['symbol'] == symbol and float(pos['positionAmt']) != 0:
                # Giá thanh lý trả về API
                return float(pos.get('liquidationPrice', 0))
        return None

    def get_margin_used(self):
        """Lấy margin đã dùng (used margin) trong tài khoản futures"""
        account = self.get_account_info()
        if not account:
            return None
        return float(account.get('totalMarginBalance', 0)) - float(account.get('availableBalance', 0))

    def get_unrealized_pnl(self, symbol: str):
        """Lấy PnL chưa thực hiện (unrealized profit/loss) của vị thế symbol"""
        pos_list = self.get_position(symbol)
        if not pos_list:
            return None
        for pos in pos_list:
            if pos['symbol'] == symbol:
                return float(pos.get('unRealizedProfit', 0))
        return None
