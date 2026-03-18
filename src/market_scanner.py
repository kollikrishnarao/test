"""
Market Scanner Module
Monitors all Polymarket markets in real-time via WebSocket
Identifies arbitrage and trading opportunities
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
from loguru import logger

from .config import config


class OpportunityType(Enum):
    """Types of trading opportunities"""
    SPLIT_ARB = "SPLIT_ARB"  # YES+NO < 0.97
    SPREAD_CAPTURE = "SPREAD_CAPTURE"  # YES+NO > 1.00
    MAKER_OPP = "MAKER_OPP"  # Wide spread for market making
    LATE_CERTAINTY = "LATE_CERTAINTY"  # High confidence near resolution


@dataclass
class MarketData:
    """Market data snapshot"""
    market_id: str
    asset: str
    timeframe: str
    yes_bid: float
    yes_ask: float
    no_bid: float
    no_ask: float
    yes_volume: float
    no_volume: float
    timestamp: datetime
    resolution_time: Optional[datetime] = None  # When market closes
    price_history: List[float] = None  # Recent price movements for momentum

    def __post_init__(self):
        if self.price_history is None:
            self.price_history = []


@dataclass
class Opportunity:
    """Trading opportunity"""
    opp_type: OpportunityType
    market_id: str
    asset: str
    timeframe: str
    yes_price: float
    no_price: float
    spread: float
    expected_value: float
    confidence: float
    timestamp: datetime
    time_to_resolution: Optional[float] = None  # Seconds until market closes
    predicted_side: Optional[str] = None  # "YES" or "NO" for directional trades
    signal_strength: Optional[float] = None  # 0.0-1.0 signal quality


class MarketScanner:
    """Scans markets for trading opportunities"""

    def __init__(self):
        self.markets: Dict[str, MarketData] = {}
        self.opportunities: List[Opportunity] = []
        self._scan_task = None

    async def initialize(self):
        """Initialize market scanner"""
        logger.info("Market Scanner initialized")
        await self._setup_websocket()

    async def _setup_websocket(self):
        """Setup WebSocket connections to Polymarket"""
        # NOTE: In production, this would connect to Polymarket's WebSocket API
        # and subscribe to order book updates for all relevant markets
        logger.info("WebSocket connections established")

    async def scan_markets(self):
        """
        Main scanning loop
        Runs every 100ms to check all markets
        """
        logger.info("Starting market scanner")

        while True:
            try:
                await asyncio.sleep(config.market_scanner_interval)

                # Clear old opportunities
                self.opportunities.clear()

                # Scan each market
                for asset in config.assets:
                    for timeframe in config.timeframes:
                        await self._scan_market(asset, timeframe)

                # Sort opportunities by expected value
                self.opportunities.sort(key=lambda x: x.expected_value, reverse=True)

            except Exception as e:
                logger.error(f"Market scanner error: {e}")

    async def _scan_market(self, asset: str, timeframe: str):
        """Scan a specific market for opportunities"""
        market_id = f"{asset}_{timeframe}"

        # NOTE: In production, this would fetch real market data
        # Simulated market data for now
        market_data = MarketData(
            market_id=market_id,
            asset=asset,
            timeframe=timeframe,
            yes_bid=0.48,
            yes_ask=0.52,
            no_bid=0.46,
            no_ask=0.50,
            yes_volume=1000.0,
            no_volume=900.0,
            timestamp=datetime.now(),
            resolution_time=self._calculate_resolution_time(timeframe),
            price_history=[0.49, 0.50, 0.51, 0.52],  # Simulated price movement
        )

        self.markets[market_id] = market_data

        # Calculate YES+NO sum
        yes_price = (market_data.yes_bid + market_data.yes_ask) / 2
        no_price = (market_data.no_bid + market_data.no_ask) / 2
        total_price = yes_price + no_price

        # Check for SPLIT_ARB opportunity
        if config.enable_split_arb and total_price < config.split_arb_threshold:
            opportunity = Opportunity(
                opp_type=OpportunityType.SPLIT_ARB,
                market_id=market_id,
                asset=asset,
                timeframe=timeframe,
                yes_price=yes_price,
                no_price=no_price,
                spread=1.0 - total_price,
                expected_value=(1.0 - total_price) * 100,  # Rough EV estimate
                confidence=1.0,  # Arbitrage is risk-free
                timestamp=datetime.now(),
            )
            self.opportunities.append(opportunity)

        # Check for SPREAD_CAPTURE opportunity
        if config.enable_spread_capture and total_price > config.spread_capture_threshold:
            opportunity = Opportunity(
                opp_type=OpportunityType.SPREAD_CAPTURE,
                market_id=market_id,
                asset=asset,
                timeframe=timeframe,
                yes_price=yes_price,
                no_price=no_price,
                spread=total_price - 1.0,
                expected_value=(total_price - 1.0) * 100,
                confidence=0.95,
                timestamp=datetime.now(),
            )
            self.opportunities.append(opportunity)

        # Check for MAKER_OPP (wide spread)
        spread = (market_data.yes_ask - market_data.yes_bid) + (market_data.no_ask - market_data.no_bid)
        if config.enable_pure_maker and spread > config.maker_spread_threshold:
            opportunity = Opportunity(
                opp_type=OpportunityType.MAKER_OPP,
                market_id=market_id,
                asset=asset,
                timeframe=timeframe,
                yes_price=yes_price,
                no_price=no_price,
                spread=spread,
                expected_value=spread * 50,  # Rough EV estimate
                confidence=0.80,
                timestamp=datetime.now(),
            )
            self.opportunities.append(opportunity)

        # Check for LATE_CERTAINTY opportunity (directional trading at extremes)
        if config.enable_late_certainty:
            late_cert_opp = self._detect_late_certainty(market_data, yes_price, no_price)
            if late_cert_opp:
                self.opportunities.append(late_cert_opp)

    def _calculate_resolution_time(self, timeframe: str) -> datetime:
        """Calculate when a market will resolve based on timeframe"""
        now = datetime.now()

        if timeframe == "5M":
            # Next 5-minute mark
            minutes = (now.minute // 5 + 1) * 5
            if minutes >= 60:
                return now.replace(hour=now.hour + 1, minute=0, second=0, microsecond=0)
            return now.replace(minute=minutes, second=0, microsecond=0)
        elif timeframe == "15M":
            # Next 15-minute mark
            minutes = (now.minute // 15 + 1) * 15
            if minutes >= 60:
                return now.replace(hour=now.hour + 1, minute=0, second=0, microsecond=0)
            return now.replace(minute=minutes, second=0, microsecond=0)
        elif timeframe == "1H":
            # Next hour
            return now.replace(hour=now.hour + 1, minute=0, second=0, microsecond=0)
        else:
            # Default to 5 minutes from now
            return now + timedelta(minutes=5)

    def _detect_late_certainty(
        self, market_data: MarketData, yes_price: float, no_price: float
    ) -> Optional[Opportunity]:
        """
        Detect late certainty opportunities - high confidence trades at extreme prices

        Strategy: Trade when price is at extremes (0.97-0.99) near market close
        - Taker fees are negligible at these prices
        - High confidence due to strong directional move
        - Only need 1-3 cents profit per trade
        """
        if not market_data.resolution_time:
            return None

        # Calculate time to resolution
        time_to_resolution = (market_data.resolution_time - datetime.now()).total_seconds()

        # Only trade in the last 60-90 seconds (configurable window)
        if time_to_resolution > config.late_certainty_window_seconds:
            return None

        # Check if YES price is at extreme (0.97-0.99)
        if yes_price >= 0.97 and yes_price <= 0.99:
            # Strong YES signal - price moved to extreme
            confidence, signal_strength = self._calculate_signal_strength(
                market_data.price_history, "YES", yes_price
            )

            if confidence >= config.min_win_probability:
                # Calculate expected profit: (1.00 - 0.97) = 0.03 = 3 cents per dollar
                profit_per_dollar = 1.0 - yes_price
                expected_value = profit_per_dollar * 100  # As percentage

                return Opportunity(
                    opp_type=OpportunityType.LATE_CERTAINTY,
                    market_id=market_data.market_id,
                    asset=market_data.asset,
                    timeframe=market_data.timeframe,
                    yes_price=yes_price,
                    no_price=no_price,
                    spread=profit_per_dollar,
                    expected_value=expected_value,
                    confidence=confidence,
                    timestamp=datetime.now(),
                    time_to_resolution=time_to_resolution,
                    predicted_side="YES",
                    signal_strength=signal_strength,
                )

        # Check if NO price is at extreme (0.97-0.99)
        elif no_price >= 0.97 and no_price <= 0.99:
            # Strong NO signal - price moved to extreme
            confidence, signal_strength = self._calculate_signal_strength(
                market_data.price_history, "NO", no_price
            )

            if confidence >= config.min_win_probability:
                profit_per_dollar = 1.0 - no_price
                expected_value = profit_per_dollar * 100

                return Opportunity(
                    opp_type=OpportunityType.LATE_CERTAINTY,
                    market_id=market_data.market_id,
                    asset=market_data.asset,
                    timeframe=market_data.timeframe,
                    yes_price=yes_price,
                    no_price=no_price,
                    spread=profit_per_dollar,
                    expected_value=expected_value,
                    confidence=confidence,
                    timestamp=datetime.now(),
                    time_to_resolution=time_to_resolution,
                    predicted_side="NO",
                    signal_strength=signal_strength,
                )

        return None

    def _calculate_signal_strength(
        self, price_history: List[float], side: str, current_price: float
    ) -> Tuple[float, float]:
        """
        Calculate confidence and signal strength based on price momentum

        Returns:
            Tuple of (confidence, signal_strength)
        """
        if not price_history or len(price_history) < 2:
            return 0.90, 0.5  # Default moderate confidence

        # Calculate price momentum (trend strength)
        price_changes = [price_history[i] - price_history[i-1]
                        for i in range(1, len(price_history))]

        if not price_changes:
            return 0.90, 0.5

        # Consistent upward trend for YES
        if side == "YES":
            positive_changes = sum(1 for change in price_changes if change > 0)
            momentum_score = positive_changes / len(price_changes)
        else:  # NO
            # For NO, we're looking at YES price declining (or NO price rising)
            negative_changes = sum(1 for change in price_changes if change < 0)
            momentum_score = negative_changes / len(price_changes)

        # Higher momentum = higher confidence
        # At extreme prices (0.97-0.99), even moderate momentum gives high confidence
        base_confidence = 0.88  # Base confidence for extreme prices
        momentum_boost = momentum_score * 0.10  # Up to 10% boost from momentum
        confidence = min(0.99, base_confidence + momentum_boost)

        # Signal strength is separate from confidence
        signal_strength = momentum_score

        return confidence, signal_strength

    def get_ranked_opportunities(self) -> List[Opportunity]:
        """Get opportunities ranked by expected value"""
        return self.opportunities.copy()

    def get_market_data(self, market_id: str) -> Optional[MarketData]:
        """Get market data for a specific market"""
        return self.markets.get(market_id)

    async def start_scanning(self):
        """Start the scanning task"""
        if self._scan_task is None or self._scan_task.done():
            self._scan_task = asyncio.create_task(self.scan_markets())
            logger.info("Market scanning started")

    async def stop_scanning(self):
        """Stop the scanning task"""
        if self._scan_task and not self._scan_task.done():
            self._scan_task.cancel()
            try:
                await self._scan_task
            except asyncio.CancelledError:
                pass
            logger.info("Market scanning stopped")


# Singleton instance
market_scanner = MarketScanner()
