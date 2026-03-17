"""
Unit tests for risk manager
"""
import pytest
from src.risk_manager import RiskManager, TradingStatus


@pytest.fixture
def risk_manager():
    """Create a fresh risk manager for each test"""
    return RiskManager()


def test_initial_capital(risk_manager):
    """Test initial capital setup"""
    assert risk_manager.available_usdc == 20.0
    assert risk_manager.deployed_usdc == 0.0
    assert risk_manager.total_capital == 20.0


def test_can_trade_with_sufficient_capital(risk_manager):
    """Test trading with sufficient capital"""
    can_trade, reason = risk_manager.can_trade(5.0)
    assert can_trade == True
    assert reason == "OK"


def test_can_trade_insufficient_capital(risk_manager):
    """Test trading with insufficient capital"""
    can_trade, reason = risk_manager.can_trade(25.0)
    assert can_trade == False
    assert "Insufficient capital" in reason


def test_can_trade_oversized(risk_manager):
    """Test trading with oversized position"""
    # Max trade size is 10% of $20 = $2
    can_trade, reason = risk_manager.can_trade(5.0)
    assert can_trade == False
    assert "exceeds max" in reason


def test_allocate_and_release_capital(risk_manager):
    """Test capital allocation and release"""
    initial_available = risk_manager.available_usdc

    # Allocate $5
    risk_manager.allocate_capital("pos1", 5.0, {"market_id": "test"})
    assert risk_manager.available_usdc == initial_available - 5.0
    assert risk_manager.deployed_usdc == 5.0
    assert len(risk_manager.open_positions) == 1

    # Release with profit
    risk_manager.release_capital("pos1", 1.0)
    assert risk_manager.available_usdc == initial_available + 1.0
    assert risk_manager.deployed_usdc == 0.0
    assert len(risk_manager.open_positions) == 0


def test_pause_and_resume(risk_manager):
    """Test pausing and resuming trading"""
    assert risk_manager.status == TradingStatus.ACTIVE

    risk_manager.pause_trading("Test pause")
    assert risk_manager.status == TradingStatus.PAUSED

    can_trade, reason = risk_manager.can_trade(1.0)
    assert can_trade == False

    risk_manager.resume_trading()
    assert risk_manager.status == TradingStatus.ACTIVE


def test_consecutive_losses(risk_manager):
    """Test consecutive loss tracking"""
    assert risk_manager.consecutive_losses == 0

    # Simulate losses
    for i in range(5):
        risk_manager.allocate_capital(f"pos{i}", 1.0, {"market_id": "test"})
        risk_manager.release_capital(f"pos{i}", -0.5)

    # After 5 losses, trading should be paused
    assert risk_manager.status == TradingStatus.PAUSED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
