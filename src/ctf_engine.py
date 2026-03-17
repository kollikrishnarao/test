"""
CTF (Conditional Token Framework) Engine
Handles split, merge, and redeem operations using Polymarket's relayer
Zero-gas, zero-fee operations for inventory management
"""
import asyncio
from typing import Dict, Tuple, Optional, List
from decimal import Decimal
from loguru import logger

try:
    from py_clob_client.client import ClobClient
    from py_clob_client.clob_types import OrderArgs
except ImportError:
    logger.warning("py-clob-client not installed. Install with: pip install py-clob-client")
    ClobClient = None

from .config import config
from .logger import trading_logger


class CTFEngine:
    """Handles CTF operations: split, merge, redeem"""

    def __init__(self, client: Optional[ClobClient] = None):
        self.client = client
        self.token_balances: Dict[str, Dict[str, float]] = {}
        self._auto_redeem_task = None

    async def initialize(self):
        """Initialize the CTF engine and client"""
        if self.client is None and ClobClient is not None:
            try:
                self.client = ClobClient(
                    host=config.polymarket_api_host,
                    key=config.polymarket_private_key,
                    chain_id=config.polymarket_chain_id,
                )
                # Create or derive API credentials
                self.client.set_api_creds(self.client.create_or_derive_api_creds())
                logger.info("CTF Engine initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize CTF Engine: {e}")
                trading_logger.log_error("CTFEngine", "InitializationError", str(e))

    async def split(self, market_id: str, amount_usdc: float) -> Tuple[float, float]:
        """
        Split USDC into YES + NO tokens for a market

        Args:
            market_id: Market identifier
            amount_usdc: Amount of USDC to split

        Returns:
            Tuple of (yes_tokens, no_tokens) received
        """
        try:
            logger.info(f"Splitting ${amount_usdc:.2f} USDC in market {market_id}")

            # NOTE: In production, this would call the actual CTF contract
            # For now, this is a placeholder that simulates the operation
            # Real implementation would use py-clob-client's CTF functions

            # Simulated split: 1 USDC -> 1 YES + 1 NO
            yes_tokens = amount_usdc
            no_tokens = amount_usdc

            # Update internal balance tracking
            if market_id not in self.token_balances:
                self.token_balances[market_id] = {"YES": 0, "NO": 0}

            self.token_balances[market_id]["YES"] += yes_tokens
            self.token_balances[market_id]["NO"] += no_tokens

            logger.success(
                f"Split successful: {amount_usdc:.2f} USDC -> "
                f"{yes_tokens:.2f} YES + {no_tokens:.2f} NO"
            )

            return (yes_tokens, no_tokens)

        except Exception as e:
            logger.error(f"Split operation failed: {e}")
            trading_logger.log_error("CTFEngine", "SplitError", str(e))
            raise

    async def merge(self, market_id: str, amount: float) -> float:
        """
        Merge YES + NO tokens back into USDC

        Args:
            market_id: Market identifier
            amount: Amount of token pairs to merge

        Returns:
            Amount of USDC received
        """
        try:
            logger.info(f"Merging {amount:.2f} token pairs in market {market_id}")

            # Check balance
            if market_id not in self.token_balances:
                raise ValueError(f"No tokens found for market {market_id}")

            yes_balance = self.token_balances[market_id].get("YES", 0)
            no_balance = self.token_balances[market_id].get("NO", 0)

            if yes_balance < amount or no_balance < amount:
                raise ValueError(
                    f"Insufficient tokens: need {amount} of each, "
                    f"have YES:{yes_balance}, NO:{no_balance}"
                )

            # NOTE: In production, this would call the actual CTF contract
            # Simulated merge: 1 YES + 1 NO -> 1 USDC
            usdc_received = amount

            # Update internal balance tracking
            self.token_balances[market_id]["YES"] -= amount
            self.token_balances[market_id]["NO"] -= amount

            logger.success(
                f"Merge successful: {amount:.2f} YES + {amount:.2f} NO -> "
                f"{usdc_received:.2f} USDC"
            )

            return usdc_received

        except Exception as e:
            logger.error(f"Merge operation failed: {e}")
            trading_logger.log_error("CTFEngine", "MergeError", str(e))
            raise

    async def redeem(self, market_id: str, outcome: str) -> float:
        """
        Redeem winning tokens after market resolution

        Args:
            market_id: Market identifier
            outcome: Winning outcome ("YES" or "NO")

        Returns:
            Amount of USDC received
        """
        try:
            logger.info(f"Redeeming {outcome} tokens in market {market_id}")

            if market_id not in self.token_balances:
                return 0.0

            token_amount = self.token_balances[market_id].get(outcome, 0)
            if token_amount == 0:
                return 0.0

            # NOTE: In production, this would call the actual CTF contract
            # Simulated redeem: 1 winning token -> 1 USDC
            usdc_received = token_amount

            # Update internal balance tracking
            self.token_balances[market_id][outcome] = 0

            logger.success(
                f"Redeem successful: {token_amount:.2f} {outcome} -> "
                f"{usdc_received:.2f} USDC"
            )

            return usdc_received

        except Exception as e:
            logger.error(f"Redeem operation failed: {e}")
            trading_logger.log_error("CTFEngine", "RedeemError", str(e))
            raise

    def get_token_balances(self, market_id: Optional[str] = None) -> Dict[str, Dict[str, float]]:
        """
        Get current token balances

        Args:
            market_id: Specific market ID, or None for all markets

        Returns:
            Dictionary of market balances
        """
        if market_id:
            return {market_id: self.token_balances.get(market_id, {"YES": 0, "NO": 0})}
        return self.token_balances.copy()

    async def auto_redeem_resolved(self):
        """
        Background task that auto-redeems all resolved winning positions every 60 seconds
        """
        logger.info("Starting auto-redeem task")

        while True:
            try:
                await asyncio.sleep(config.auto_redeem_interval)

                # NOTE: In production, this would:
                # 1. Query Polymarket API for resolved markets
                # 2. Check which ones we have positions in
                # 3. Call redeem() for each winning position

                # For now, this is a placeholder
                logger.debug("Auto-redeem check completed")

            except Exception as e:
                logger.error(f"Auto-redeem task error: {e}")
                trading_logger.log_error("CTFEngine", "AutoRedeemError", str(e))
                await asyncio.sleep(config.auto_redeem_interval)

    async def start_auto_redeem(self):
        """Start the auto-redeem background task"""
        if self._auto_redeem_task is None or self._auto_redeem_task.done():
            self._auto_redeem_task = asyncio.create_task(self.auto_redeem_resolved())
            logger.info("Auto-redeem task started")

    async def stop_auto_redeem(self):
        """Stop the auto-redeem background task"""
        if self._auto_redeem_task and not self._auto_redeem_task.done():
            self._auto_redeem_task.cancel()
            try:
                await self._auto_redeem_task
            except asyncio.CancelledError:
                pass
            logger.info("Auto-redeem task stopped")

    def calculate_split_cost(self, amount: float) -> float:
        """Calculate cost of split operation (always $0)"""
        return 0.0

    def calculate_merge_cost(self, amount: float) -> float:
        """Calculate cost of merge operation (always $0)"""
        return 0.0

    def calculate_redeem_cost(self, amount: float) -> float:
        """Calculate cost of redeem operation (always $0)"""
        return 0.0


# Example usage and testing
async def main():
    """Test the CTF Engine"""
    engine = CTFEngine()
    await engine.initialize()

    # Test split
    yes, no = await engine.split("test_market_1", 10.0)
    print(f"Split: 10 USDC -> {yes} YES + {no} NO")

    # Check balances
    balances = engine.get_token_balances("test_market_1")
    print(f"Balances: {balances}")

    # Test merge
    usdc = await engine.merge("test_market_1", 5.0)
    print(f"Merge: 5 YES + 5 NO -> {usdc} USDC")

    # Check balances again
    balances = engine.get_token_balances("test_market_1")
    print(f"Balances after merge: {balances}")

    # Test redeem
    usdc = await engine.redeem("test_market_1", "YES")
    print(f"Redeem: {usdc} USDC")


if __name__ == "__main__":
    asyncio.run(main())
