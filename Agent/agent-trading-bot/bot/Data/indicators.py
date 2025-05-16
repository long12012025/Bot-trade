import pandas as pd
import numpy as np
from typing import List, Dict


def to_dataframe(candles: List[Dict]) -> pd.DataFrame:
    """
    Chuyển danh sách nến dạng dict thành DataFrame.
    """
    df = pd.DataFrame(candles)
    df["open_time"] = pd.to_datetime(df["open_time"])
    df.set_index("open_time", inplace=True)
    return df


def add_ema(df: pd.DataFrame, period: int = 14, column: str = "close") -> pd.DataFrame:
    df[f"ema_{period}"] = df[column].ewm(span=period, adjust=False).mean()
    return df


def add_rsi(df: pd.DataFrame, period: int = 14, column: str = "close") -> pd.DataFrame:
    delta = df[column].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / (avg_loss + 1e-10)  # tránh chia 0
    df[f"rsi_{period}"] = 100 - (100 / (1 + rs))
    return df


def add_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9, column: str = "close") -> pd.DataFrame:
    ema_fast = df[column].ewm(span=fast, adjust=False).mean()
    ema_slow = df[column].ewm(span=slow, adjust=False).mean()
    df["macd"] = ema_fast - ema_slow
    df["macd_signal"] = df["macd"].ewm(span=signal, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]
    return df


def add_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0, column: str = "close") -> pd.DataFrame:
    sma = df[column].rolling(window=period).mean()
    std = df[column].rolling(window=period).std()

    df["bb_upper"] = sma + std_dev * std
    df["bb_lower"] = sma - std_dev * std
    df["bb_middle"] = sma
    return df


def calculate_all_indicators(candles: List[Dict]) -> pd.DataFrame:
    """
    Hàm tổng hợp tính toàn bộ chỉ báo kỹ thuật cần thiết.
    """
    df = to_dataframe(candles)
    df = add_ema(df, 20)
    df = add_ema(df, 50)
    df = add_rsi(df, 14)
    df = add_macd(df)
    df = add_bollinger_bands(df)
    return df.dropna()
