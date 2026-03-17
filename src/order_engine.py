"""
Order Engine Module
Handles order placement, cancellation, and execution strategies
Supports maker orders (earn rebates) and strategic taker orders (extreme prices only)
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from loguru import logger

try:
    from py_clob_client.client import ClobClient
    from py_clob_client.clob_types import OrderArgs
except ImportError:
    logger.warning("py-clob-client not installed")
    ClobClient = None
    OrderArgs = None

from .config import config, calculate_fee_at_price, is_taker_fee_acceptable
from .logger import trading_logger
from .ctf_engine import CTFEngine


class OrderSide(Enum):
    """Order side"""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """Order type"""
    MAKER = "MAKER"  # Limit order, earns rebate
    TAKER = "TAKER"  # Market order, pays fee


@dataclass
class Order:
    """Order data class"""
    order_id: str
    market_id: str
    side: OrderSide
    price: float
    size: float
    order_type: OrderType
    timestamp: datetime
    filled: bool = False
    cancelled: bool = False


class OrderEngine:
    """Manages order placement and execution"""

    def __init__(self, client: Optional[ClobClient] = None, ctf_engine: Optional[CTFEngine] = None):
        self.client = client
        self.ctf_engine = ctf_engine
        self.open_orders: Dict[str, Order] = {}
        self.order_counter: int = 0
        self._cancel_stale_task = None

    async def initialize(self):
        """Initialize the order engine"""
        logger.info("Order Engine initialized")

    async def place_maker_order(
        self,
        market_id: str,
        side: OrderSide,
        price: float,
        size: float
    ) -> Optional[str]:
        """
        Place a maker limit order

        Args:
            market_id: Market identifier
            side: Order side (BUY/SELL)
            price: Limit price
            size: Order size

        Returns:
            Order ID if successful, None otherwise
        """
        try:
            # Validate price doesn't cross spread (maker only)
            # In production, this would check current order book

            self.order_counter += 1
            order_id = f"order_{self.order_counter}_{datetime.now().timestamp()}"

            order = Order(
                order_id=order_id,
                market_id=market_id,
                side=side,
                price=price,
                size=size,
                order_type=OrderType.MAKER,
                timestamp=datetime.now(),
            )

            self.open_orders[order_id] = order

            logger.info(
                f"Maker order placed: {side.value} {size} @ ${price:.3f} "
                f"in market {market_id} | Order ID: {order_id}"
            )

            # Log to database
            trading_logger.log_trade({
                "market_id": market_id,
                "market_name": market_id,
                "strategy_type": "MAKER",
                "side": side.value,
                "price": price,
                "size": size,
                "fee_paid": 0,  # Maker doesn't pay fees
                "rebate_earned": 0,  # Will be updated when filled
                "net_pnl": 0,
                "route_used": "MAKER_ORDER",
                "order_id": order_id,
            })

            return order_id

        except Exception as e:
            logger.error(f"Failed to place maker order: {e}")
            trading_logger.log_error("OrderEngine", "MakerOrderError", str(e))
            return None

    async def place_taker_order(
        self,
        market_id: str,
        side: OrderSide,
        size: float,
        max_slippage: float = None
    ) -> Optional[str]:
        """
        Place a taker market order (ONLY at extreme prices where fees are low)

        Args:
            market_id: Market identifier
            side: Order side (BUY/SELL)
            size: Order size
            max_slippage: Maximum acceptable slippage (default from config)

        Returns:
            Order ID if successful, None otherwise
        """
        try:
            if max_slippage is None:
                max_slippage = config.max_slippage_percent / 100

            # Get current market price (simulated for now)
            # In production, this would query the order book
            current_price = 0.50  # Placeholder

            # Check if fee is acceptable
            if not is_taker_fee_acceptable(current_price):
                logger.warning(
                    f"Taker fee too high at price ${current_price:.3f}, "
                    f"fee would be {calculate_fee_at_price(current_price)*100:.2f}%"
                )
                return None

            self.order_counter += 1
            order_id = f"order_{self.order_counter}_{datetime.now().timestamp()}"

            order = Order(
                order_id=order_id,
                market_id=market_id,
                side=side,
                price=current_price,
                size=size,
                order_type=OrderType.TAKER,
                timestamp=datetime.now(),
            )

            self.open_orders[order_id] = order

            # Calculate fee
            fee = calculate_fee_at_price(current_price) * size * current_price

            logger.info(
                f"Taker order placed: {side.value} {size} @ ${current_price:.3f} "
                f"in market {market_id} | Fee: ${fee:.4f} | Order ID: {order_id}"
            )

            # Log to database
            trading_logger.log_trade({
                "market_id": market_id,
                "market_name": market_id,
                "strategy_type": "TAKER",
                "side": side.value,
                "price": current_price,
                "size": size,
                "fee_paid": fee,
                "rebate_earned": 0,
                "net_pnl": -fee,  # Fee is a cost
                "route_used": "TAKER_ORDER",
                "order_id": order_id,
            })

            return order_id

        except Exception as e:
            logger.error(f"Failed to place taker order: {e}")
            trading_logger.log_error("OrderEngine", "TakerOrderError", str(e))
            return None

    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order

        Args:
            order_id: Order identifier

        Returns:
            True if cancelled successfully
        """
        try:
            if order_id not in self.open_orders:
                logger.warning(f"Order {order_id} not found")
                return False

            order = self.open_orders[order_id]

            if order.filled:
                logger.warning(f"Order {order_id} already filled")
                return False

            order.cancelled = True
            del self.open_orders[order_id]

            logger.info(f"Order cancelled: {order_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            trading_logger.log_error("OrderEngine", "CancelOrderError", str(e))
            return False

    async def cancel_all_stale(self):
        """
        Background task to cancel stale orders (> 45 seconds old)
        """
        logger.info("Starting cancel stale orders task")

        while True:
            try:
                await asyncio.sleep(config.cancel_stale_interval)

                now = datetime.now()
                stale_threshold = timedelta(seconds=config.cancel_stale_order_seconds)

                stale_orders = [
                    order_id
                    for order_id, order in self.open_orders.items()
                    if not order.filled and (now - order.timestamp) > stale_threshold
                ]

                for order_id in stale_orders:
                    logger.warning(f"Cancelling stale order: {order_id}")
                    await self.cancel_order(order_id)

                if stale_orders:
                    logger.info(f"Cancelled {len(stale_orders)} stale orders")

            except Exception as e:
                logger.error(f"Cancel stale task error: {e}")
                trading_logger.log_error("OrderEngine", "CancelStaleError", str(e))

    async def split_and_sell_strategy(
        self,
        market_id: str,
        target_side: str,
        amount: float,
        sell_price: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Split-and-sell strategy: acquire target tokens at near-zero cost

        Process:
        1. Split USDC into YES + NO tokens (zero fee)
        2. Sell the unwanted side as a maker order (earn rebate)
        3. Hold the target side at effective zero cost + rebate income

        Args:
            market_id: Market identifier
            target_side: Side to hold ("YES" or "NO")
            amount: Amount of USDC to split
            sell_price: Price to sell unwanted side

        Returns:
            Tuple of (success, order_id)
        """
        try:
            if not self.ctf_engine:
                logger.error("CTF engine not available")
                return False, None

            logger.info(
                f"Executing split-and-sell: ${amount:.2f} USDC, "
                f"target={target_side}, sell_price=${sell_price:.3f}"
            )

            # Step 1: Split USDC into YES + NO tokens
            yes_tokens, no_tokens = await self.ctf_engine.split(market_id, amount)

            # Step 2: Determine which side to sell
            sell_side = "NO" if target_side == "YES" else "YES"
            sell_amount = no_tokens if sell_side == "NO" else yes_tokens

            # Step 3: Place maker order to sell unwanted side
            order_side = OrderSide.SELL
            order_id = await self.place_maker_order(
                market_id=market_id,
                side=order_side,
                price=sell_price,
                size=sell_amount
            )

            if order_id:
                logger.success(
                    f"Split-and-sell executed: Holding {target_side} {amount}, "
                    f"Selling {sell_side} {sell_amount} @ ${sell_price:.3f}"
                )
                return True, order_id
            else:
                logger.error("Failed to place sell order after split")
                return False, None

        except Exception as e:
            logger.error(f"Split-and-sell strategy failed: {e}")
            trading_logger.log_error("OrderEngine", "SplitAndSellError", str(e))
            return False, None

    async def start_cancel_stale(self):
        """Start the cancel stale orders task"""
        if self._cancel_stale_task is None or self._cancel_stale_task.done():
            self._cancel_stale_task = asyncio.create_task(self.cancel_all_stale())
            logger.info("Cancel stale orders task started")

    async def stop_cancel_stale(self):
        """Stop the cancel stale orders task"""
        if self._cancel_stale_task and not self._cancel_stale_task.done():
            self._cancel_stale_task.cancel()
            try:
                await self._cancel_stale_task
            except asyncio.CancelledError:
                pass
            logger.info("Cancel stale orders task stopped")

    def get_open_orders(self, market_id: Optional[str] = None) -> List[Order]:
        """Get all open orders, optionally filtered by market"""
        if market_id:
            return [
                order
                for order in self.open_orders.values()
                if order.market_id == market_id and not order.filled and not order.cancelled
            ]
        return [
            order
            for order in self.open_orders.values()
            if not order.filled and not order.cancelled
        ]

    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        return self.open_orders.get(order_id)


# Example usage
async def main():
    """Test the Order Engine"""
    from .ctf_engine import CTFEngine

    ctf = CTFEngine()
    await ctf.initialize()

    engine = OrderEngine(ctf_engine=ctf)
    await engine.initialize()

    # Test maker order
    order_id = await engine.place_maker_order(
        market_id="test_market",
        side=OrderSide.BUY,
        price=0.55,
        size=10.0
    )
    print(f"Placed maker order: {order_id}")

    # Test split-and-sell
    success, sell_order_id = await engine.split_and_sell_strategy(
        market_id="test_market",
        target_side="YES",
        amount=5.0,
        sell_price=0.60
    )
    print(f"Split-and-sell: success={success}, order={sell_order_id}")

    # Check open orders
    open_orders = engine.get_open_orders()
    print(f"Open orders: {len(open_orders)}")


if __name__ == "__main__":
    asyncio.run(main())
