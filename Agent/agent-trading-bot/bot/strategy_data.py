# strategy_data.py

class Strategy:
    def __init__(self, name, leverage, max_position_size, stop_loss_pct, take_profit_pct, description):
        """
        name: tên chiến lược
        leverage: đòn bẩy cố định hoặc tối đa
        max_position_size: khối lượng tối đa trên mỗi lệnh (BTC hoặc USDT)
        stop_loss_pct: % dừng lỗ so với giá entry (ví dụ 0.01 = 1%)
        take_profit_pct: % chốt lời so với giá entry
        description: mô tả chiến lược, cách vận hành
        """
        self.name = name
        self.leverage = leverage
        self.max_position_size = max_position_size
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.description = description

    def to_dict(self):
        return {
            "name": self.name,
            "leverage": self.leverage,
            "max_position_size": self.max_position_size,
            "stop_loss_pct": self.stop_loss_pct,
            "take_profit_pct": self.take_profit_pct,
            "description": self.description
        }


class StrategyData:
    # Danh sách chiến lược cố định, chỉnh sửa tùy ý
    STRATEGIES = [
        Strategy(
            name="Scalping 5m Tight SL",
            leverage=10,
            max_position_size=0.01,
            stop_loss_pct=0.005,
            take_profit_pct=0.01,
            description="Scalping trên khung 5 phút với SL nhỏ, TP gấp đôi SL, phù hợp thị trường biến động nhẹ."
        ),
        Strategy(
            name="Breakout Momentum",
            leverage=15,
            max_position_size=0.02,
            stop_loss_pct=0.01,
            take_profit_pct=0.02,
            description="Chiến lược breakout dựa trên nến đóng trên kháng cự, áp dụng đòn bẩy vừa phải."
        ),
        Strategy(
            name="Mean Reversion",
            leverage=8,
            max_position_size=0.015,
            stop_loss_pct=0.007,
            take_profit_pct=0.012,
            description="Dự đoán giá hồi về trung bình, phù hợp khi giá biến động quá mạnh trong thời gian ngắn."
        ),
        Strategy(
            name="Trend Following",
            leverage=12,
            max_position_size=0.025,
            stop_loss_pct=0.015,
            take_profit_pct=0.03,
            description="Theo xu hướng dài hạn, đòn bẩy vừa phải, đặt SL rộng hơn để tránh bị quét quá sớm."
        ),
        Strategy(
            name="Swing Trading 1h",
            leverage=6,
            max_position_size=0.03,
            stop_loss_pct=0.02,
            take_profit_pct=0.04,
            description="Swing trading trên khung 1 giờ, đặt SL và TP phù hợp với biến động dài hơn."
        ),
        Strategy(
            name="High Risk High Reward",
            leverage=20,
            max_position_size=0.01,
            stop_loss_pct=0.03,
            take_profit_pct=0.06,
            description="Đòn bẩy cao, SL rộng, TP cao, chỉ dành cho nhà đầu tư chấp nhận rủi ro lớn."
        ),
        Strategy(
            name="Conservative Long Term",
            leverage=5,
            max_position_size=0.05,
            stop_loss_pct=0.01,
            take_profit_pct=0.05,
            description="Chiến lược dài hạn, đòn bẩy thấp, khối lượng lớn hơn, ít giao dịch hơn."
        ),
        Strategy(
            name="Range Bound",
            leverage=10,
            max_position_size=0.02,
            stop_loss_pct=0.008,
            take_profit_pct=0.015,
            description="Giao dịch trong biên độ giá cố định, tận dụng vùng hỗ trợ và kháng cự."
        ),
        Strategy(
            name="News Driven",
            leverage=15,
            max_position_size=0.015,
            stop_loss_pct=0.02,
            take_profit_pct=0.03,
            description="Chiến lược theo tin tức, phản ứng nhanh với các biến động lớn do tin tức."
        ),
        Strategy(
            name="Grid Trading",
            leverage=8,
            max_position_size=0.04,
            stop_loss_pct=0.0,
            take_profit_pct=0.0,
            description="Đặt nhiều lệnh mua và bán quanh vùng giá để kiếm lời từ dao động nhỏ."
        ),
    ]

    @classmethod
    def get_strategy_by_name(cls, name):
        for strat in cls.STRATEGIES:
            if strat.name == name:
                return strat
        return None

    @classmethod
    def list_all_strategies(cls):
        return [s.to_dict() for s in cls.STRATEGIES]
