import time
import hmac
import hashlib
import requests
import logging
from urllib.parse import urlencode

class BinanceFuturesAPI:
    BASE_URL = "https://fapi.binance.com"

    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        self.session.headers.update({
            "X-MBX-APIKEY": self.api_key
        })

    def _get_timestamp(self):
        return int(time.time() * 1000)

    def _sign_payload(self, params: dict):
        query_string = urlencode(params)
        signature = hmac.new(self.api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
        return signature

    def _request(self, method, path, params=None, signed=False):
        if params is None:
            params = {}

        url = self.BASE_URL + path

        if signed:
            params['timestamp'] = self._get_timestamp()
            params['signature'] = self._sign_payload(params)

        try:
            if method == "GET":
                response = self.session.get(url, params=params, timeout=10)
            elif method == "POST":
                response = self.session.post(url, params=params, timeout=10)
            elif method == "DELETE":
                response = self.session.delete(url, params=params, timeout=10)
            else:
                raise ValueError(f"Unsupported method {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP error {e.response.status_code}: {e.response.text}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Request exception: {e}")

        return None

    # --- Public Endpoints ---

    def get_server_time(self):
        return self._request("GET", "/fapi/v1/time")

    def get_order_book(self, symbol: str, limit=100):
        params = {"symbol": symbol.upper(), "limit": limit}
        return self._request("GET", "/fapi/v1/depth", params=params)

    def get_klines(self, symbol: str, interval: str, limit=500):
        params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
        return self._request("GET", "/fapi/v1/klines", params=params)

    # --- Signed Endpoints ---

    def get_account_info(self):
        return self._request("GET", "/fapi/v2/account", signed=True)

    def get_position(self, symbol: str):
        data = self.get_account_info()
        if data and "positions" in data:
            for pos in data["positions"]:
                if pos["symbol"] == symbol.upper():
                    return pos
        return None

    def set_leverage(self, symbol: str, leverage: int):
        params = {"symbol": symbol.upper(), "leverage": leverage}
        return self._request("POST", "/fapi/v1/leverage", params=params, signed=True)

    def place_order(self, symbol: str, side: str, order_type: str, quantity: float,
                    price: float = None, time_in_force: str = "GTC", reduce_only: bool = False,
                    close_position: bool = False, stop_price: float = None):
        """
        Đặt lệnh futures.
        side: BUY or SELL
        order_type: MARKET, LIMIT, STOP_MARKET, TAKE_PROFIT_MARKET, v.v.
        reduce_only: nếu True, lệnh sẽ chỉ giảm vị thế (close position)
        close_position: nếu True, đóng toàn bộ position hiện có
        """
        params = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": order_type.upper(),
            "quantity": quantity,
            "reduceOnly": str(reduce_only).lower(),
            "closePosition": str(close_position).lower()
        }
        if order_type.upper() == "LIMIT":
            if price is None:
                raise ValueError("Price phải được cung cấp cho lệnh LIMIT")
            params["price"] = price
            params["timeInForce"] = time_in_force

        if stop_price is not None:
            params["stopPrice"] = stop_price

        return self._request("POST", "/fapi/v1/order", params=params, signed=True)

    def cancel_order(self, symbol: str, order_id: int = None, orig_client_order_id: str = None):
        """
        Huỷ lệnh theo orderId hoặc clientOrderId.
        """
        if order_id is None and orig_client_order_id is None:
            raise ValueError("Phải cung cấp order_id hoặc orig_client_order_id")

        params = {"symbol": symbol.upper()}
        if order_id is not None:
            params["orderId"] = order_id
        if orig_client_order_id is not None:
            params["origClientOrderId"] = orig_client_order_id

        return self._request("DELETE", "/fapi/v1/order", params=params, signed=True)

    def get_open_orders(self, symbol: str = None):
        params = {}
        if symbol:
            params["symbol"] = symbol.upper()
        return self._request("GET", "/fapi/v1/openOrders", params=params, signed=True)

    def get_position_mode(self):
        return self._request("GET", "/fapi/v1/positionSide/dual", signed=True)

    def set_position_mode(self, dual_side_position: bool):
        params = {"dualSidePosition": "true" if dual_side_position else "false"}
        return self._request("POST", "/fapi/v1/positionSide/dual", params=params, signed=True)

    def get_balance(self):
        info = self.get_account_info()
        if info and "assets" in info:
            return info["assets"]
        return None

    def get_usdt_balance(self):
        assets = self.get_balance()
        if assets:
            for asset in assets:
                if asset["asset"] == "USDT":
                    return float(asset["walletBalance"])
        return 0.0

# Example usage:
# api = BinanceFuturesAPI(api_key="your_api_key", api_secret="your_api_secret")
# print(api.get_server_time())
# print(api.get_klines("BTCUSDT", "5m", 10))
# print(api.set_leverage("BTCUSDT", 20))
# print(api.place_order("BTCUSDT", "BUY", "MARKET", 0.001))
