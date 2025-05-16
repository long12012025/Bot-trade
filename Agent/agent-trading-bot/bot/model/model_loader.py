import torch
import os
from model.model_def import MyModel

def create_model(
    input_dim: int,
    hidden_dim: int = 64,
    lstm_layers: int = 2,
    fc_dim: int = 32,
    dropout_lstm: float = 0.3,
    dropout_fc: float = 0.3,
    num_classes: int = 3,
    bidirectional: bool = False,
    clip_grad_norm: float = 1.0,
    device: torch.device = torch.device("cpu"),
) -> MyModel:
    """
    Khởi tạo model MyModel với tham số cho trước,
    chuyển model sang device (CPU hoặc GPU).
    """
    model = MyModel(
        input_dim=input_dim,
        hidden_dim=hidden_dim,
        lstm_layers=lstm_layers,
        fc_dim=fc_dim,
        dropout_lstm=dropout_lstm,
        dropout_fc=dropout_fc,
        num_classes=num_classes,
        bidirectional=bidirectional,
        clip_grad_norm=clip_grad_norm,
    )
    model.to(device)
    return model

def load_checkpoint(model: MyModel, checkpoint_path: str, device: torch.device):
    """
    Load trọng số model từ checkpoint, trả về model đã load.
    Nếu file không tồn tại hoặc lỗi, trả về model chưa thay đổi.
    """
    if not os.path.exists(checkpoint_path):
        print(f"Checkpoint file {checkpoint_path} không tồn tại, dùng model mới khởi tạo.")
        return model

    try:
        checkpoint = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(checkpoint)
        print(f"Đã load checkpoint từ {checkpoint_path}")
    except Exception as e:
        print(f"Lỗi khi load checkpoint: {e}")
    return model

def save_checkpoint(model: MyModel, checkpoint_path: str):
    """
    Lưu trọng số model xuống file checkpoint_path.
    """
    try:
        torch.save(model.state_dict(), checkpoint_path)
        print(f"Đã lưu checkpoint tại {checkpoint_path}")
    except Exception as e:
        print(f"Lỗi khi lưu checkpoint: {e}")
