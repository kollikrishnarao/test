"""
Unit tests for config module
"""
import pytest
from src.config import (
    config,
    calculate_max_trade_size,
    calculate_compounding_rate,
    calculate_fee_at_price,
    is_taker_fee_acceptable
)


def test_config_loaded():
    """Test that configuration is loaded"""
    assert config.starting_capital == 20.0
    assert config.hourly_profit_target == 1.0
    assert len(config.assets) == 4
    assert len(config.timeframes) == 3


def test_max_trade_size():
    """Test max trade size calculation"""
    capital = 100.0
    max_size = calculate_max_trade_size(capital)
    assert max_size == 10.0  # 10% of 100


def test_compounding_rate():
    """Test compounding rate calculation"""
    # Below $50: 100% reinvest
    assert calculate_compounding_rate(40.0) == 1.0

    # Between $50-200: 70% reinvest
    assert calculate_compounding_rate(100.0) == 0.7

    # Above $200: 50% reinvest
    assert calculate_compounding_rate(300.0) == 0.5


def test_fee_at_price():
    """Test fee calculation at different price points"""
    # Fee should be highest at 0.50
    fee_50 = calculate_fee_at_price(0.50)
    assert fee_50 == pytest.approx(0.0156, rel=0.01)

    # Fee should be lower at extremes
    fee_10 = calculate_fee_at_price(0.10)
    assert fee_10 < fee_50

    fee_90 = calculate_fee_at_price(0.90)
    assert fee_90 < fee_50

    # Fee should be near zero at very low/high prices
    fee_01 = calculate_fee_at_price(0.01)
    assert fee_01 < 0.001

    fee_99 = calculate_fee_at_price(0.99)
    assert fee_99 < 0.001


def test_taker_fee_acceptable():
    """Test taker fee acceptability"""
    # Should be acceptable at extreme prices
    assert is_taker_fee_acceptable(0.05) == True
    assert is_taker_fee_acceptable(0.95) == True

    # Should NOT be acceptable at mid prices
    assert is_taker_fee_acceptable(0.50) == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
