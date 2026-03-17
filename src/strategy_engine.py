"""
Strategy Engine Module
Evaluates opportunities and executes trading strategies
Main decision-making component of the bot
"""
import asyncio
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

from .config import config, calculate_fee_at_price
from .market_scanner import market_scanner, OpportunityType, Opportunity
from .price_oracle import price_oracle
from .ctf_engine import CTFEngine
from .order_engine import OrderEngine, OrderSide
from .risk_manager import risk_manager
from .logger import trading_logger


@dataclass
class Decision:
    """Trading decision"""
    execute: bool
    opportunity: Optional[Opportunity]
    size: float
    strategy_type: str
    reason: str


class StrategyEngine:
    """Evaluates and executes trading strategies"""

    def __init__(
        self,
        ctf_engine: CTFEngine,
        order_engine: OrderEngine
    ):
        self.ctf_engine = ctf_engine
        self.order_engine = order_engine
        self._strategy_task = None

    async def initialize(self):
        """Initialize strategy engine"""
        logger.info("Strategy Engine initialized")

    async def run(self):
        """
        Main strategy loop
        Runs every 100ms to evaluate opportunities
        """
        logger.info("Starting strategy engine")

        while True:
            try:
                await asyncio.sleep(config.strategy_loop_interval)

                # Get opportunities from market scanner
                opportunities = market_scanner.get_ranked_opportunities()

                # Get oracle flags
                oracle_flags = price_oracle.get_flags()

                # Get current balances
                balances = self.ctf_engine.get_token_balances()

                # Get available capital
                capital = risk_manager.available_usdc

                # Evaluate each opportunity
                for opportunity in opportunities:
                    decision = await self.evaluate_opportunity(
                        opportunity, capital, balances
                    )

                    if decision.execute:
                        await self.execute_strategy(decision)
                        break  # Execute one at a time

            except Exception as e:
                logger.error(f"Strategy engine error: {e}")
                trading_logger.log_error("StrategyEngine", "StrategyError", str(e))

    async def evaluate_opportunity(
        self,
        opportunity: Opportunity,
        capital: float,
        balances: Dict
    ) -> Decision:
        """
        Evaluate an opportunity and decide whether to execute

        Args:
            opportunity: Trading opportunity
            capital: Available capital
            balances: Current token balances

        Returns:
            Trading decision
        """
        try:
            # Check if trading is allowed
            can_trade, reason = risk_manager.can_trade(1.0)  # Check with $1 first
            if not can_trade:
                return Decision(
                    execute=False,
                    opportunity=opportunity,
                    size=0,
                    strategy_type=opportunity.opp_type.value,
                    reason=reason
                )

            # Calculate position size based on strategy type
            if opportunity.opp_type == OpportunityType.SPLIT_ARB:
                # Split arbitrage: maximum size allowed
                size = await self._calculate_split_arb_size(opportunity, capital)
                execute = size > 0

            elif opportunity.opp_type == OpportunityType.SPREAD_CAPTURE:
                # Spread capture: moderate size
                size = await self._calculate_spread_capture_size(opportunity, capital)
                execute = size > 0

            elif opportunity.opp_type == OpportunityType.MAKER_OPP:
                # Market making: conservative size
                size = await self._calculate_maker_size(opportunity, capital)
                execute = size > 0

            elif opportunity.opp_type == OpportunityType.LATE_CERTAINTY:
                # Late certainty: high confidence directional trade at extremes
                size = await self._calculate_late_certainty_size(opportunity, capital)
                execute = size > 0

            else:
                size = 0
                execute = False

            # Final check with actual size
            if execute and size > 0:
                can_trade, reason = risk_manager.can_trade(size)
                if not can_trade:
                    return Decision(
                        execute=False,
                        opportunity=opportunity,
                        size=size,
                        strategy_type=opportunity.opp_type.value,
                        reason=reason
                    )

            return Decision(
                execute=execute,
                opportunity=opportunity,
                size=size,
                strategy_type=opportunity.opp_type.value,
                reason="OK" if execute else "No opportunity"
            )

        except Exception as e:
            logger.error(f"Opportunity evaluation failed: {e}")
            return Decision(
                execute=False,
                opportunity=opportunity,
                size=0,
                strategy_type=opportunity.opp_type.value,
                reason=f"Error: {e}"
            )

    async def _calculate_split_arb_size(
        self, opportunity: Opportunity, capital: float
    ) -> float:
        """Calculate position size for split arbitrage"""
        # Split arbitrage is risk-free, use maximum allowed size
        max_size = min(capital * 0.10, config.starting_capital * 0.50)  # Up to 50% of starting capital
        return max_size

    async def _calculate_spread_capture_size(
        self, opportunity: Opportunity, capital: float
    ) -> float:
        """Calculate position size for spread capture"""
        # Spread capture has some risk, use Kelly fraction
        win_prob = opportunity.confidence
        gross_return = opportunity.spread
        kelly = (win_prob * gross_return - (1 - win_prob)) / gross_return
        kelly_fraction = kelly * config.kelly_fraction  # Fractional Kelly

        size = capital * kelly_fraction
        max_size = capital * 0.05  # Max 5% per trade
        return min(size, max_size)

    async def _calculate_maker_size(
        self, opportunity: Opportunity, capital: float
    ) -> float:
        """Calculate position size for market making"""
        # Market making: small, frequent trades
        return capital * 0.03  # 3% per trade

    async def _calculate_late_certainty_size(
        self, opportunity: Opportunity, capital: float
    ) -> float:
        """
        Calculate position size for late certainty trades

        These are high-confidence directional trades at extreme prices
        Use larger size due to high win probability and low risk
        """
        # Base size on confidence and signal strength
        confidence = opportunity.confidence
        signal_strength = opportunity.signal_strength or 0.5

        # Higher confidence = larger position
        # At 0.88 confidence: ~15% of capital
        # At 0.95 confidence: ~25% of capital
        confidence_multiplier = (confidence - 0.85) / 0.15  # Scale 0.85-1.0 to 0-1
        confidence_multiplier = max(0, min(1, confidence_multiplier))

        base_size = capital * 0.15  # Base 15% per trade
        confidence_boost = capital * 0.10 * confidence_multiplier  # Up to +10%
        size = base_size + confidence_boost

        # Cap at 25% of capital per trade
        max_size = capital * 0.25
        return min(size, max_size)

    async def execute_strategy(self, decision: Decision):
        """
        Execute a trading strategy

        Args:
            decision: Trading decision to execute
        """
        try:
            opportunity = decision.opportunity
            size = decision.size

            logger.info(
                f"Executing {decision.strategy_type}: {opportunity.asset} {opportunity.timeframe}, "
                f"Size: ${size:.2f}"
            )

            # Allocate capital
            position_id = f"pos_{opportunity.market_id}_{datetime.now().timestamp()}"
            risk_manager.allocate_capital(
                position_id,
                size,
                {
                    "market_id": opportunity.market_id,
                    "strategy": decision.strategy_type,
                }
            )

            # Execute based on strategy type
            if opportunity.opp_type == OpportunityType.SPLIT_ARB:
                await self._execute_split_arb(opportunity, size, position_id)

            elif opportunity.opp_type == OpportunityType.SPREAD_CAPTURE:
                await self._execute_spread_capture(opportunity, size, position_id)

            elif opportunity.opp_type == OpportunityType.MAKER_OPP:
                await self._execute_maker(opportunity, size, position_id)

            elif opportunity.opp_type == OpportunityType.LATE_CERTAINTY:
                await self._execute_late_certainty(opportunity, size, position_id)

        except Exception as e:
            logger.error(f"Strategy execution failed: {e}")
            trading_logger.log_error("StrategyEngine", "ExecutionError", str(e))

    async def _execute_split_arb(
        self, opportunity: Opportunity, size: float, position_id: str
    ):
        """Execute split arbitrage strategy"""
        # 1. Split USDC into YES + NO
        yes, no = await self.ctf_engine.split(opportunity.market_id, size)

        # 2. Sell both sides as maker orders
        # Sell YES at yes_ask, sell NO at no_ask
        await self.order_engine.place_maker_order(
            opportunity.market_id, OrderSide.SELL, opportunity.yes_price, yes
        )
        await self.order_engine.place_maker_order(
            opportunity.market_id, OrderSide.SELL, opportunity.no_price, no
        )

        # 3. Expected profit: (YES+NO sold) - 1.00 USDC spent
        expected_profit = (opportunity.yes_price + opportunity.no_price - 1.0) * size

        # Release capital (simulated completion)
        risk_manager.release_capital(position_id, expected_profit)

        logger.success(f"Split arbitrage executed: Expected profit ${expected_profit:.2f}")

    async def _execute_spread_capture(
        self, opportunity: Opportunity, size: float, position_id: str
    ):
        """Execute spread capture strategy"""
        # Use split-and-sell to post both sides as maker
        await self.order_engine.split_and_sell_strategy(
            opportunity.market_id,
            "YES",  # Target side
            size,
            opportunity.no_price
        )

        # Simulated completion
        expected_profit = opportunity.spread * size
        risk_manager.release_capital(position_id, expected_profit)

        logger.success(f"Spread capture executed: Expected profit ${expected_profit:.2f}")

    async def _execute_maker(
        self, opportunity: Opportunity, size: float, position_id: str
    ):
        """Execute market making strategy"""
        # Post limit orders on both sides
        await self.order_engine.place_maker_order(
            opportunity.market_id,
            OrderSide.BUY,
            opportunity.yes_price - 0.02,
            size / opportunity.yes_price
        )
        await self.order_engine.place_maker_order(
            opportunity.market_id,
            OrderSide.SELL,
            opportunity.yes_price + 0.02,
            size / opportunity.yes_price
        )

        # Simulated completion
        expected_profit = opportunity.spread * 0.25 * size  # Partial capture
        risk_manager.release_capital(position_id, expected_profit)

        logger.success(f"Maker strategy executed: Expected profit ${expected_profit:.2f}")

    async def _execute_late_certainty(
        self, opportunity: Opportunity, size: float, position_id: str
    ):
        """
        Execute late certainty directional trade

        Strategy: Buy the predicted winning side at extreme price (0.97-0.99)
        - Use taker order (market order) since we're at extremes where fees are low
        - Expected profit: 1-3 cents per dollar
        - High confidence (>88%) ensures high win rate
        """
        predicted_side = opportunity.predicted_side
        target_price = opportunity.yes_price if predicted_side == "YES" else opportunity.no_price

        logger.info(
            f"Late certainty trade: {predicted_side} @ ${target_price:.3f}, "
            f"Confidence: {opportunity.confidence:.1%}, "
            f"Time to resolution: {opportunity.time_to_resolution:.0f}s"
        )

        # Calculate fee at this extreme price (should be negligible)
        fee_percent = calculate_fee_at_price(target_price)
        fee_amount = fee_percent * size

        # Place taker order (market order) to buy the winning side
        order_side = OrderSide.BUY
        await self.order_engine.place_taker_order(
            opportunity.market_id,
            order_side,
            size / target_price  # Convert dollar amount to shares
        )

        # Calculate expected profit
        # If we buy at 0.97, we get $1.00 at resolution = $0.03 profit per dollar
        profit_per_dollar = 1.0 - target_price
        gross_profit = profit_per_dollar * size
        net_profit = gross_profit - fee_amount

        # Log the trade
        trading_logger.log_trade({
            "market_id": opportunity.market_id,
            "market_name": f"{opportunity.asset}_{opportunity.timeframe}",
            "strategy_type": "LATE_CERTAINTY",
            "side": predicted_side,
            "price": target_price,
            "size": size / target_price,
            "fee_paid": fee_amount,
            "rebate_earned": 0,
            "net_pnl": net_profit,
            "route_used": "TAKER_EXTREME",
            "order_id": position_id,
        })

        # Release capital (simulated completion at resolution)
        risk_manager.release_capital(position_id, net_profit)

        logger.success(
            f"Late certainty executed: {predicted_side} @ ${target_price:.3f} | "
            f"Expected profit: ${net_profit:.2f} (fee: ${fee_amount:.4f})"
        )

    async def start_strategy(self):
        """Start the strategy engine task"""
        if self._strategy_task is None or self._strategy_task.done():
            self._strategy_task = asyncio.create_task(self.run())
            logger.info("Strategy engine started")

    async def stop_strategy(self):
        """Stop the strategy engine task"""
        if self._strategy_task and not self._strategy_task.done():
            self._strategy_task.cancel()
            try:
                await self._strategy_task
            except asyncio.CancelledError:
                pass
            logger.info("Strategy engine stopped")
