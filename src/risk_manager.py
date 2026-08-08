"""
Risk Manager Module
Tracks capital, enforces limits, manages compounding, and handles emergencies
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from .config import config, calculate_max_trade_size, calculate_compounding_rate
from .logger import trading_logger


class TradingStatus(Enum):
    """Trading status enum"""
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    EMERGENCY = "EMERGENCY"


@dataclass
class CapitalSnapshot:
    """Snapshot of capital at a point in time"""
    timestamp: datetime
    available_usdc: float
    deployed_usdc: float
    token_holdings_value: float
    total_capital: float


class RiskManager:
    """Manages risk, capital, and trading limits"""

    def __init__(self):
        self.available_usdc: float = config.starting_capital
        self.deployed_usdc: float = 0.0
        self.token_holdings_value: float = 0.0
        self.status: TradingStatus = TradingStatus.ACTIVE

        # Hour tracking
        self.hour_start: datetime = datetime.now().replace(minute=0, second=0, microsecond=0)
        self.hour_start_capital: float = config.starting_capital
        self.hour_trades: int = 0

        # Day tracking
        self.day_start: datetime = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.day_start_capital: float = config.starting_capital

        # Position tracking
        self.open_positions: Dict[str, Dict] = {}
        self.position_counter: int = 0

        # Emergency tracking
        self.consecutive_losses: int = 0
        self.last_error_time: Optional[datetime] = None

        self._monitor_task = None

    @property
    def total_capital(self) -> float:
        """Calculate total capital including deployed and token holdings"""
        return self.available_usdc + self.deployed_usdc + self.token_holdings_value

    @property
    def hour_pnl(self) -> float:
        """Calculate PnL for current hour"""
        return self.total_capital - self.hour_start_capital

    @property
    def day_pnl(self) -> float:
        """Calculate PnL for current day"""
        return self.total_capital - self.day_start_capital

    @property
    def hourly_target_met(self) -> bool:
        """Check if hourly target is met"""
        return self.hour_pnl >= config.hourly_profit_target

    def get_snapshot(self) -> CapitalSnapshot:
        """Get current capital snapshot"""
        return CapitalSnapshot(
            timestamp=datetime.now(),
            available_usdc=self.available_usdc,
            deployed_usdc=self.deployed_usdc,
            token_holdings_value=self.token_holdings_value,
            total_capital=self.total_capital,
        )

    def can_trade(self, amount: float) -> Tuple[bool, str]:
        """
        Check if a trade of given amount can be executed

        Returns:
            Tuple of (can_trade, reason)
        """
        # Check trading status
        if self.status == TradingStatus.STOPPED:
            return False, "Trading is stopped"

        if self.status == TradingStatus.PAUSED:
            return False, "Trading is paused"

        if self.status == TradingStatus.EMERGENCY:
            return False, "Emergency mode - trading disabled"

        # Check available capital
        if amount > self.available_usdc:
            return False, f"Insufficient capital: need ${amount:.2f}, have ${self.available_usdc:.2f}"

        # Check single trade size limit
        max_trade = calculate_max_trade_size(self.total_capital)
        if amount > max_trade:
            return False, f"Trade size ${amount:.2f} exceeds max ${max_trade:.2f}"

        # Check concurrent positions limit
        if len(self.open_positions) >= config.max_concurrent_positions:
            return False, f"Max concurrent positions ({config.max_concurrent_positions}) reached"

        # Check hourly loss limit
        if abs(self.hour_pnl) >= config.hourly_loss_limit and self.hour_pnl < 0:
            self.pause_trading("Hourly loss limit reached")
            return False, f"Hourly loss limit reached: ${abs(self.hour_pnl):.2f}"

        # Check daily loss limit
        if abs(self.day_pnl) >= config.daily_loss_limit and self.day_pnl < 0:
            self.stop_trading("Daily loss limit reached")
            return False, f"Daily loss limit reached: ${abs(self.day_pnl):.2f}"

        return True, "OK"

    def allocate_capital(self, position_id: str, amount: float, market_info: Dict):
        """Allocate capital to a position"""
        if position_id in self.open_positions:
            logger.warning(f"Position {position_id} already exists")
            return

        self.available_usdc -= amount
        self.deployed_usdc += amount
        self.open_positions[position_id] = {
            "amount": amount,
            "market_id": market_info.get("market_id"),
            "entry_time": datetime.now(),
            "strategy": market_info.get("strategy"),
        }
        self.position_counter += 1

        logger.info(
            f"Capital allocated: ${amount:.2f} to position {position_id} | "
            f"Available: ${self.available_usdc:.2f}, Deployed: ${self.deployed_usdc:.2f}"
        )

    def release_capital(self, position_id: str, pnl: float):
        """Release capital from a closed position"""
        if position_id not in self.open_positions:
            logger.warning(f"Position {position_id} not found")
            return

        position = self.open_positions[position_id]
        amount = position["amount"]

        self.deployed_usdc -= amount
        self.available_usdc += amount + pnl
        self.hour_trades += 1

        # Track consecutive losses
        if pnl < 0:
            self.consecutive_losses += 1
            if self.consecutive_losses >= 5:
                self.pause_trading(f"Too many consecutive losses: {self.consecutive_losses}")
        else:
            self.consecutive_losses = 0

        del self.open_positions[position_id]

        logger.info(
            f"Capital released: ${amount:.2f} from position {position_id}, PnL: ${pnl:.2f} | "
            f"Available: ${self.available_usdc:.2f}"
        )

    def update_token_holdings_value(self, value: float):
        """Update the value of token holdings"""
        self.token_holdings_value = value

    def reset_hourly_tracking(self):
        """Reset hourly tracking (called at start of each hour)"""
        current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)

        if current_hour > self.hour_start:
            # Log hour completion
            trading_logger.update_hourly_pnl(
                self.hour_start_capital,
                self.total_capital,
                self.hour_trades
            )

            if self.hourly_target_met:
                logger.success(
                    f"✅ Hourly target MET! PnL: ${self.hour_pnl:.2f} | "
                    f"Capital: ${self.total_capital:.2f}"
                )
            else:
                logger.warning(
                    f"⚠️ Hourly target MISSED. PnL: ${self.hour_pnl:.2f} | "
                    f"Target: ${config.hourly_profit_target:.2f}"
                )

            # Apply compounding
            self.apply_compounding()

            # Reset for new hour
            self.hour_start = current_hour
            self.hour_start_capital = self.total_capital
            self.hour_trades = 0

    def reset_daily_tracking(self):
        """Reset daily tracking (called at start of each day)"""
        current_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        if current_day > self.day_start:
            logger.info(
                f"📊 Daily Summary: PnL: ${self.day_pnl:.2f} | "
                f"Start: ${self.day_start_capital:.2f} | "
                f"End: ${self.total_capital:.2f}"
            )

            self.day_start = current_day
            self.day_start_capital = self.total_capital

    def apply_compounding(self):
        """Apply compounding logic based on capital level"""
        if self.hour_pnl > 0:
            compound_rate = calculate_compounding_rate(self.total_capital)
            reinvest_amount = self.hour_pnl * compound_rate
            bank_amount = self.hour_pnl * (1 - compound_rate)

            logger.info(
                f"💰 Compounding: Reinvest ${reinvest_amount:.2f} ({compound_rate*100:.0f}%), "
                f"Bank ${bank_amount:.2f}"
            )

    def pause_trading(self, reason: str):
        """Pause trading"""
        self.status = TradingStatus.PAUSED
        logger.warning(f"🔴 Trading PAUSED: {reason}")
        trading_logger.log_error("RiskManager", "TradingPaused", reason)

    def resume_trading(self):
        """Resume trading"""
        self.status = TradingStatus.ACTIVE
        logger.info("✅ Trading RESUMED")

    def stop_trading(self, reason: str):
        """Stop trading completely"""
        self.status = TradingStatus.STOPPED
        logger.error(f"🛑 Trading STOPPED: {reason}")
        trading_logger.log_error("RiskManager", "TradingStopped", reason)

    def emergency_stop(self, reason: str):
        """Emergency stop - requires manual intervention"""
        self.status = TradingStatus.EMERGENCY
        logger.critical(f"🚨 EMERGENCY STOP: {reason}")
        trading_logger.log_error("RiskManager", "EmergencyStop", reason)

    def handle_api_error(self, error: Exception):
        """Handle API errors"""
        logger.error(f"API Error: {error}")
        self.last_error_time = datetime.now()
        trading_logger.log_error("RiskManager", "APIError", str(error))

        # Pause trading for 30 seconds
        self.pause_trading("API error occurred")

    def handle_position_stuck(self, position_id: str):
        """Handle stuck position"""
        logger.error(f"Position {position_id} is stuck")
        trading_logger.log_error("RiskManager", "PositionStuck", f"Position {position_id}")

    def handle_network_failure(self):
        """Handle network failure"""
        logger.error("Network failure detected")
        self.pause_trading("Network failure")
        trading_logger.log_error("RiskManager", "NetworkFailure", "Network connection lost")

    def handle_oracle_stale(self):
        """Handle stale oracle"""
        logger.warning("Oracle data is stale")
        trading_logger.log_error("RiskManager", "OracleStale", "Oracle not updating")

    async def monitor(self):
        """Background monitoring task"""
        logger.info("Starting risk monitor")

        while True:
            try:
                await asyncio.sleep(config.risk_monitor_interval)

                # Check hour/day rollovers
                self.reset_hourly_tracking()
                self.reset_daily_tracking()

                # Check if paused trading can be resumed
                if (
                    self.status == TradingStatus.PAUSED
                    and self.last_error_time
                    and (datetime.now() - self.last_error_time).seconds > 30
                ):
                    self.resume_trading()
                    self.last_error_time = None

                # Log status
                logger.debug(
                    f"Risk Monitor: Capital=${self.total_capital:.2f}, "
                    f"Hour PnL=${self.hour_pnl:.2f}, "
                    f"Day PnL=${self.day_pnl:.2f}, "
                    f"Positions={len(self.open_positions)}, "
                    f"Status={self.status.value}"
                )

            except Exception as e:
                logger.error(f"Risk monitor error: {e}")
                trading_logger.log_error("RiskManager", "MonitorError", str(e))

    async def start_monitoring(self):
        """Start the monitoring task"""
        if self._monitor_task is None or self._monitor_task.done():
            self._monitor_task = asyncio.create_task(self.monitor())
            logger.info("Risk monitoring started")

    async def stop_monitoring(self):
        """Stop the monitoring task"""
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            logger.info("Risk monitoring stopped")


# Singleton instance
risk_manager = RiskManager()
