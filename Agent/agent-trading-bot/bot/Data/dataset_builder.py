import pandas as pd
import numpy as np
from typing import Tuple


class DatasetBuilder:
    def __init__(self, df: pd.DataFrame, future_shift: int = 3, threshold: float = 0.002):
        """
        :param df: DataFrame đã có cột chỉ báo như close, RSI, EMA, MACD,...
        :param future_shift: Số nến sau để dự đoán (ví dụ tăng sau 3 nến)
        :param threshold: Ngưỡng tăng để tính là BUY (ví dụ: 0.002 = 0.2%)
        """
        self.df = df.copy()
        self.future_shift = future_shift
        self.threshold = threshold

    def create_labels(self) -> pd.DataFrame:
        """
        Thêm cột 'label' với giá trị:
            1  = BUY (giá tăng trên ngưỡng)
            -1 = SELL (giảm mạnh)
            0  = HOLD (biến động yếu)
        """
        self.df["future_close"] = self.df["close"].shift(-self.future_shift)
        self.df["future_return"] = (self.df["future_close"] - self.df["close"]) / self.df["close"]

        def classify(r):
            if r > self.threshold:
                return 1  # BUY
            elif r < -self.threshold:
                return -1  # SELL
            else:
                return 0  # HOLD

        self.df["label"] = self.df["future_return"].apply(classify)
        return self.df.dropna().reset_index(drop=True)

    def build_features_and_labels(self, drop_cols: list = ["timestamp", "open_time", "close_time", "future_close", "future_return"]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Trả về X (features) và y (labels) đã sẵn sàng để train.
        """
        df_labeled = self.create_labels()

        # Loại bỏ các cột không cần thiết
        features = df_labeled.drop(columns=(drop_cols + ["label"]), errors='ignore')
        labels = df_labeled["label"]

        # Chuẩn hóa dữ liệu (optional): có thể scale về 0-1 nếu dùng MLP/CNN
        # from sklearn.preprocessing import StandardScaler
        # scaler = StandardScaler()
        # features = scaler.fit_transform(features)

        return features.values, labels.values
