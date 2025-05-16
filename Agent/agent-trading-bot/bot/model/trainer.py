import torch
import torch.nn.functional as F
from tqdm import tqdm
import logging
import os

from data.dataset_builder import get_train_val_loaders  # chỉ dùng dữ liệu lịch sử

class Trainer:
    def __init__(
        self,
        model: torch.nn.Module,
        device: torch.device,
        clip_grad_norm: float = 1.0,
        checkpoint_path: str = "model_checkpoint.pt",
        lr: float = 1e-3,
        verbose: bool = True,
        save_best_only: bool = True,
    ):
        self.model = model.to(device)
        self.device = device
        self.clip_grad_norm = clip_grad_norm
        self.checkpoint_path = checkpoint_path
        self.verbose = verbose
        self.save_best_only = save_best_only

        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        self.criterion = torch.nn.CrossEntropyLoss()
        self.best_val_loss = float("inf")

    def _train_one_batch(self, inputs, targets):
        self.model.train()
        inputs = inputs.to(self.device)
        targets = targets.to(self.device)

        self.optimizer.zero_grad()
        outputs = self.model(inputs)
        loss = self.criterion(outputs, targets)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.clip_grad_norm)
        self.optimizer.step()

        preds = outputs.argmax(dim=1)
        correct = (preds == targets).sum().item()
        return loss.item(), correct, targets.size(0)

    def train_one_epoch(self, train_loader):
        running_loss = 0.0
        total_correct = 0
        total_samples = 0

        loop = tqdm(train_loader, desc="Training", leave=False) if self.verbose else train_loader
        for batch_idx, (inputs, targets) in enumerate(loop):
            loss, correct, batch_size = self._train_one_batch(inputs, targets)
            running_loss += loss
            total_correct += correct
            total_samples += batch_size

            if self.verbose and batch_idx % 10 == 0:
                loop.set_postfix(loss=running_loss / (batch_idx + 1), accuracy=total_correct / total_samples)

        avg_loss = running_loss / len(train_loader)
        avg_acc = total_correct / total_samples
        return avg_loss, avg_acc

    def validate(self, val_loader):
        if val_loader is None:
            logging.warning("Validation loader is None, skipping validation.")
            return None, None

        self.model.eval()
        val_loss = 0.0
        val_correct = 0
        val_samples = 0
        with torch.no_grad():
            for inputs, targets in val_loader:
                inputs = inputs.to(self.device)
                targets = targets.to(self.device)
                outputs = self.model(inputs)
                loss = self.criterion(outputs, targets)

                val_loss += loss.item()
                preds = outputs.argmax(dim=1)
                val_correct += (preds == targets).sum().item()
                val_samples += targets.size(0)

        avg_val_loss = val_loss / len(val_loader)
        avg_val_acc = val_correct / val_samples
        logging.info(f"Validation loss: {avg_val_loss:.4f}, accuracy: {avg_val_acc:.4f}")
        return avg_val_loss, avg_val_acc

    def save_checkpoint(self):
        try:
            torch.save(self.model.state_dict(), self.checkpoint_path)
            logging.info(f"Model checkpoint saved to {self.checkpoint_path}")
        except Exception as e:
            logging.error(f"Error saving checkpoint: {e}")

    def load_checkpoint(self):
        if os.path.exists(self.checkpoint_path):
            try:
                self.model.load_state_dict(torch.load(self.checkpoint_path, map_location=self.device))
                logging.info(f"Loaded checkpoint from {self.checkpoint_path}")
            except Exception as e:
                logging.error(f"Error loading checkpoint: {e}")
        else:
            logging.warning(f"Checkpoint {self.checkpoint_path} not found")

    def train_offline(self, epochs: int, batch_size: int = 64):
        train_loader, val_loader = get_train_val_loaders(batch_size=batch_size)

        for epoch in range(1, epochs + 1):
            logging.info(f"Starting epoch {epoch}")
            train_loss, train_acc = self.train_one_epoch(train_loader)
            logging.info(f"Epoch {epoch} train loss: {train_loss:.4f}, accuracy: {train_acc:.4f}")

            if val_loader:
                val_loss, val_acc = self.validate(val_loader)
                if val_loss is not None and val_loss < self.best_val_loss:
                    self.best_val_loss = val_loss
                    if self.save_best_only:
                        self.save_checkpoint()
            else:
                # Nếu không có val_loader thì lưu checkpoint cuối cùng
                self.save_checkpoint()

            logging.info(f"Finished epoch {epoch}")
