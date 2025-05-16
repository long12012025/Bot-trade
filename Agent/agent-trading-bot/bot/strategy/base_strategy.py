from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def should_open_position(self, candle) -> bool:
        """Kiểm tra điều kiện mở vị thế mới"""
        pass

    @abstractmethod
    def should_close_position(self, candle) -> bool:
        """Kiểm tra điều kiện đóng vị thế hiện tại"""
        pass

    @abstractmethod
    def get_signal_type(self, candle) -> str:
        """Trả về loại tín hiệu: 'long' hoặc 'short'"""
        pass
