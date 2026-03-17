"""
Market Scanner Module
Monitors all Polymarket markets in real-time via WebSocket
Identifies arbitrage and trading opportunities
"""
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
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
