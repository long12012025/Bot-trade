import torch
import torch.nn as nn
import torch.nn.functional as F

def init_lstm_weights(lstm):
    """
    Khởi tạo trọng số cho LSTM:
    - weight_ih dùng Xavier uniform
    - weight_hh dùng Orthogonal
    - bias forget gate set = 1
    """
    for name, param in lstm.named_parameters():
        if 'weight_ih' in name:
            nn.init.xavier_uniform_(param.data)
        elif 'weight_hh' in name:
            nn.init.orthogonal_(param.data)
        elif 'bias' in name:
            param.data.fill_(0)
            n = param.size(0)
            param.data[n//4:n//2].fill_(1.0)  # forget gate bias

class MyModel(nn.Module):
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 128,
        lstm_layers: int = 2,
        fc_dim: int = 64,
        dropout_lstm: float = 0.3,
        dropout_fc: float = 0.3,
        num_classes: int = 3,
        bidirectional: bool = False,
        clip_grad_norm: float = 1.0,
    ):
        super().__init__()

        self.bidirectional = bidirectional
        self.clip_grad_norm = clip_grad_norm

        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=lstm_layers,
            batch_first=True,
            dropout=dropout_lstm if lstm_layers > 1 else 0,
            bidirectional=bidirectional,
        )
        init_lstm_weights(self.lstm)

        lstm_output_dim = hidden_dim * 2 if bidirectional else hidden_dim
        self.layer_norm = nn.LayerNorm(lstm_output_dim)

        self.fc1 = nn.Linear(lstm_output_dim, fc_dim)
        self.bn1 = nn.BatchNorm1d(fc_dim)
        self.relu = nn.ReLU()
        self.dropout_fc = nn.Dropout(dropout_fc)
        self.fc2 = nn.Linear(fc_dim, num_classes)

        self._init_weights()

    def _init_weights(self):
        nn.init.xavier_uniform_(self.fc1.weight)
        nn.init.zeros_(self.fc1.bias)
        nn.init.xavier_uniform_(self.fc2.weight)
        nn.init.zeros_(self.fc2.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.ndim != 3:
            raise ValueError(f"Input phải có shape [batch, seq_len, features], nhận {x.shape}")
        if x.dtype != torch.float32:
            raise TypeError(f"Input dtype phải là float32, nhận {x.dtype}")

        lstm_out, _ = self.lstm(x)
        last_hidden = lstm_out[:, -1, :]  # Lấy hidden cuối cùng

        normed = self.layer_norm(last_hidden)

        fc1_out = self.fc1(normed)
        # BatchNorm1d expects input shape [batch, features]
        bn_out = self.bn1(fc1_out)
        relu_out = self.relu(bn_out)
        drop_out = self.dropout_fc(relu_out)

        # Residual connection nếu cùng kích thước
        if drop_out.shape == normed.shape:
            out = drop_out + normed
        else:
            out = drop_out

        out = self.fc2(out)
        return out

    def clip_gradients(self):
        torch.nn.utils.clip_grad_norm_(self.parameters(), self.clip_grad_norm)
