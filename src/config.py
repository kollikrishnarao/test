"""
Configuration module for Polymarket Trading Bot
All configurable parameters centralized here
"""
import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Config(BaseSettings):
    """Main configuration class"""

    # Polymarket API Configuration
    polymarket_api_host: str = Field(default="https://clob.polymarket.com", env="POLYMARKET_API_HOST")
    polymarket_chain_id: int = Field(default=137, env="POLYMARKET_CHAIN_ID")
    polymarket_private_key: str = Field(default="", env="POLYMARKET_PRIVATE_KEY")

    # Polygon RPC Configuration
    polygon_rpc_url: str = Field(default="https://polygon-rpc.com", env="POLYGON_RPC_URL")

    # Binance API Configuration
    binance_api_key: str = Field(default="", env="BINANCE_API_KEY")
    binance_api_secret: str = Field(default="", env="BINANCE_API_SECRET")

    # Telegram Configuration
    telegram_bot_token: str = Field(default="", env="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", env="TELEGRAM_CHAT_ID")

    # Trading Parameters
    starting_capital: float = Field(default=20.0, env="STARTING_CAPITAL")
    hourly_profit_target: float = Field(default=1.0, env="HOURLY_PROFIT_TARGET")
    max_single_trade_percent: float = Field(default=10.0, env="MAX_SINGLE_TRADE_PERCENT")
    max_concurrent_positions: int = Field(default=6, env="MAX_CONCURRENT_POSITIONS")
    hourly_loss_limit: float = Field(default=2.0, env="HOURLY_LOSS_LIMIT")
    daily_loss_limit: float = Field(default=5.0, env="DAILY_LOSS_LIMIT")

    # Asset Configuration
    assets: List[str] = ["BTC", "ETH", "SOL", "XRP"]
    timeframes: List[str] = ["5M", "15M", "1H"]

    # Strategy Configuration
    enable_split_arb: bool = Field(default=True, env="ENABLE_SPLIT_ARB")
    enable_spread_capture: bool = Field(default=True, env="ENABLE_SPREAD_CAPTURE")
    enable_late_certainty: bool = Field(default=True, env="ENABLE_LATE_CERTAINTY")
    enable_pure_maker: bool = Field(default=True, env="ENABLE_PURE_MAKER")
    enable_directional: bool = Field(default=False, env="ENABLE_DIRECTIONAL")

    # Risk Management
    kelly_fraction: float = Field(default=0.25, env="KELLY_FRACTION")
    min_win_probability: float = Field(default=0.88, env="MIN_WIN_PROBABILITY")
    max_slippage_percent: float = Field(default=0.3, env="MAX_SLIPPAGE_PERCENT")

    # Fee Thresholds
    split_arb_threshold: float = 0.97  # YES+NO < 0.97 triggers split arb
    spread_capture_threshold: float = 1.00  # YES+NO > 1.00 triggers spread capture
    maker_spread_threshold: float = 0.04  # Min spread for maker orders
    extreme_price_low: float = 0.10  # Below this, taker fees are acceptable
    extreme_price_high: float = 0.90  # Above this, taker fees are acceptable
    max_taker_fee_percent: float = 0.30  # Never take if fee > 0.30%

    # Timing
    late_certainty_window_seconds: int = 90  # Last 90s before resolution
    oracle_lag_threshold_percent: float = 1.5  # Min price movement for oracle lag
    cancel_stale_order_seconds: int = 45  # Cancel orders older than 45s

    # Loop intervals (seconds)
    strategy_loop_interval: float = 0.1  # 100ms main loop
    market_scanner_interval: float = 0.1  # 100ms market scan
    oracle_update_interval: float = 1.0  # 1s oracle check
    auto_redeem_interval: float = 60.0  # 60s auto-redeem check
    cancel_stale_interval: float = 30.0  # 30s stale order cleanup
    risk_monitor_interval: float = 5.0  # 5s risk monitoring

    # Compounding Logic
    compound_threshold_1: float = 50.0  # Below $50: 100% reinvest
    compound_threshold_2: float = 200.0  # $50-200: 70% reinvest
    compound_rate_full: float = 1.0  # 100% reinvestment
    compound_rate_high: float = 0.7  # 70% reinvestment
    compound_rate_low: float = 0.5  # 50% reinvestment

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    database_path: str = Field(default="trades.db", env="DATABASE_PATH")

    # Performance
    max_websocket_retries: int = 5
    websocket_retry_delay: float = 2.0
    api_timeout: float = 10.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton config instance
config = Config()


def get_config() -> Config:
    """Get configuration instance"""
    return config


def calculate_max_trade_size(capital: float) -> float:
    """Calculate maximum trade size based on current capital"""
    return capital * (config.max_single_trade_percent / 100.0)


def calculate_compounding_rate(capital: float) -> float:
    """Calculate compounding rate based on capital level"""
    if capital <= config.compound_threshold_1:
        return config.compound_rate_full
    elif capital <= config.compound_threshold_2:
        return config.compound_rate_high
    else:
        return config.compound_rate_low


def calculate_fee_at_price(price: float) -> float:
    """
    Calculate Polymarket taker fee at a given price point
    Fee curve peaks at 1.56% at $0.50 and drops to ~0% at extremes
    """
    # Symmetric bell curve approximation
    # Maximum fee is 1.56% at price = 0.50
    # Drops symmetrically toward 0% as price approaches 0.01 or 0.99

    if price <= 0.01 or price >= 0.99:
        return 0.0

    # Distance from 0.50 (center of bell curve)
    distance = abs(price - 0.50)

    # Approximate fee curve using quadratic function
    # At 0.50: fee = 1.56%
    # At 0.40/0.60: fee = 1.44%
    # At 0.30/0.70: fee = 1.10%
    # At 0.20/0.80: fee = 0.64%
    # At 0.10/0.90: fee = 0.20%
    # At 0.05/0.95: fee = 0.05%

    max_fee = 0.0156
    fee = max_fee * (1 - (distance / 0.49) ** 2)

    return max(0.0, fee)


def is_taker_fee_acceptable(price: float) -> bool:
    """Check if taker fee at given price is acceptable"""
    fee_percent = calculate_fee_at_price(price) * 100
    return fee_percent <= config.max_taker_fee_percent


if __name__ == "__main__":
    # Test configuration
    print("Configuration loaded:")
    print(f"Starting Capital: ${config.starting_capital}")
    print(f"Hourly Target: ${config.hourly_profit_target}")
    print(f"Assets: {config.assets}")
    print(f"Timeframes: {config.timeframes}")
    print("\nFee curve examples:")
    for price in [0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95]:
        fee = calculate_fee_at_price(price)
        print(f"  Price ${price:.2f}: Fee {fee*100:.2f}%")
