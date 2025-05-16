import torch
import torch.nn.functional as F
import pandas as pd
import numpy as np
from model.model_def import MyModel
from model.model_loader import load_model
from data.indicators import calculate_all_indicators
import logging
import os

class Predictor:
    def __init__(self, model_path: str = "model_checkpoint.pt", sequence_length: int = 60, threshold: float = 0.7):
        self.model_path = model_path
        self.sequence_length = sequence_length
        self.threshold = threshold

        if not os.path.exists(self.model_path):
            logging.error(f"[Predictor] Không tìm thấy model checkpoint tại '{self.model_path}' - Dừng giao dịch.")
            raise FileNotFoundError(f"Model checkpoint '{self.model_path}' not found.")

        try:
            self.model = load_model(self.model_path)
            self.model.eval()
            logging.info(f"[Predictor] Mô hình được load từ {self.model_path}")
        except Exception as e:
            logging.error(f"[Predictor] Lỗi load mô hình: {e} - Dừng giao dịch.")
            raise

    def preprocess(self, df: pd.DataFrame) -> torch.Tensor:
        if len(df) < self.sequence_length:
            logging.warning(f"[Predictor] Dữ liệu đầu vào ngắn hơn {self.sequence_length}. Đang padding...")
            pad_df = pd.concat([df.iloc[[0]].copy()] * (self.sequence_length - len(df)) + [df])
        else:
            pad_df = df[-self.sequence_length:]

        try:
            features = pad_df.select_dtypes(include=[np.number])
            tensor = torch.tensor(features.values, dtype=torch.float32)
            return tensor.unsqueeze(0)  # shape: [1, seq_len, features]
        except Exception as e:
            logging.error(f"[Predictor] Lỗi khi xử lý dữ liệu đầu vào: {e} - Dừng giao dịch.")
            raise

    def predict_action(self, df: pd.DataFrame) -> str:
        try:
            df = calculate_all_indicators(df)
            input_tensor = self.preprocess(df)

            with torch.no_grad():
                output = self.model(input_tensor)
                probs = F.softmax(output, dim=1).cpu().numpy().flatten()

            actions = ["BUY", "SELL", "HOLD"]
            action_idx = int(np.argmax(probs))
            confidence = float(probs[action_idx])

            logging.info(f"[Predictor] Dự đoán: {actions[action_idx]} | Xác suất: {confidence:.4f}")

            if confidence < self.threshold:
                logging.info("[Predictor] Xác suất thấp hơn ngưỡng, giữ trạng thái HOLD.")
                return "HOLD"

            return actions[action_idx]

        except Exception as e:
            logging.error(f"[Predictor] Lỗi dự đoán hành động: {e} - Dừng giao dịch.")
            return "HOLD"

    def get_action_probabilities(self, df: pd.DataFrame) -> dict:
        try:
            df = calculate_all_indicators(df)
            input_tensor = self.preprocess(df)

            with torch.no_grad():
                output = self.model(input_tensor)
                probs = F.softmax(output, dim=1).cpu().numpy().flatten()

            return {"BUY": float(probs[0]), "SELL": float(probs[1]), "HOLD": float(probs[2])}

        except Exception as e:
            logging.error(f"[Predictor] Lỗi lấy xác suất hành động: {e} - Trả về mặc định HOLD.")
            return {"BUY": 0.0, "SELL": 0.0, "HOLD": 1.0}
