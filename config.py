"""
Configuration file for Fear & Greed DCA Bot

Modify these parameters to customize the strategy behavior.
"""

from dataclasses import dataclass


@dataclass
class BotConfig:
    """
    Main configuration for the Fear & Greed DCA Bot

    Fear & Greed Index Scale:
    - 0-24: Extreme Fear (strong buy signal)
    - 25-44: Fear (buy signal)
    - 45-55: Neutral
    - 56-75: Greed (consider selling)
    - 76-100: Extreme Greed (strong sell signal)
    """

    # Strategy Thresholds
    buy_threshold: int = 25
    """When F&G index is <= this value, execute DCA buy orders"""

    sell_threshold: int = 75
    """When F&G index is >= this value, sell entire position"""

    # Position Sizing
    order_size_pct: float = 5.0
    """Percentage of current equity to invest per buy signal (e.g., 5.0 = 5%)"""

    # Capital & Fees
    initial_capital: float = 10_000.0
    """Starting capital in USD"""

    fee_rate: float = 0.0005
    """Trading fee rate per side (0.0005 = 0.05%, typical for Binance maker)"""

    # Risk-Free Rate (for Sharpe/Sortino calculations)
    risk_free_rate: float = 0.02
    """Annual risk-free rate for ratio calculations (0.02 = 2%)"""

    # Optimization Ranges (for parameter sweeps)
    buy_threshold_range: list = None
    """Range of buy thresholds to test (None = default [15,20,25,30,35])"""

    sell_threshold_range: list = None
    """Range of sell thresholds to test (None = default [65,70,75,80,85])"""

    def __post_init__(self):
        """Set default ranges if not provided"""
        if self.buy_threshold_range is None:
            self.buy_threshold_range = [15, 20, 25, 30, 35]
        if self.sell_threshold_range is None:
            self.sell_threshold_range = [65, 70, 75, 80, 85]

    def validate(self):
        """Validate configuration parameters"""
        errors = []

        if not 0 <= self.buy_threshold <= 100:
            errors.append("buy_threshold must be between 0 and 100")

        if not 0 <= self.sell_threshold <= 100:
            errors.append("sell_threshold must be between 0 and 100")

        if self.buy_threshold >= self.sell_threshold:
            errors.append("buy_threshold must be less than sell_threshold")

        if self.order_size_pct <= 0 or self.order_size_pct > 100:
            errors.append("order_size_pct must be between 0 and 100")

        if self.initial_capital <= 0:
            errors.append("initial_capital must be positive")

        if self.fee_rate < 0 or self.fee_rate > 0.1:
            errors.append("fee_rate must be between 0 and 0.1 (10%)")

        if errors:
            raise ValueError("Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

        return True


# Predefined strategy configurations

CONSERVATIVE = BotConfig(
    buy_threshold=30,      # Buy only during stronger fear
    sell_threshold=70,     # Sell earlier when greed emerges
    order_size_pct=3.0,    # Smaller position sizes
    initial_capital=10_000.0,
    fee_rate=0.0005
)

MODERATE = BotConfig(
    buy_threshold=25,      # Standard fear level
    sell_threshold=75,     # Standard greed level
    order_size_pct=5.0,    # Moderate position sizes
    initial_capital=10_000.0,
    fee_rate=0.0005
)

AGGRESSIVE = BotConfig(
    buy_threshold=20,      # Buy on milder fear
    sell_threshold=80,     # Only sell on extreme greed
    order_size_pct=7.0,    # Larger position sizes
    initial_capital=10_000.0,
    fee_rate=0.0005
)

EXTREME = BotConfig(
    buy_threshold=15,      # Only buy on extreme fear
    sell_threshold=85,     # Only sell on extreme greed
    order_size_pct=10.0,   # Very large position sizes
    initial_capital=10_000.0,
    fee_rate=0.0005
)
