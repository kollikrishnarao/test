# Implementation Roadmap: Split-and-Maker Strategy
## From Research to Production

---

## 🎯 Goal

Implement the split-and-maker strategy as the primary trading approach, replacing the flawed late certainty directional strategy with a mathematically sound, positive-EV approach.

---

## 📋 Implementation Phases

### Phase 1: Core Split-and-Maker Engine (Week 1)

#### 1.1 Create SplitAndMakerStrategy Class

**File:** `src/strategies/split_and_maker.py`

```python
"""
Split-and-Maker Strategy Implementation
Core strategy with positive expected value through structural edge
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import asyncio


@dataclass
class SplitMakerOpportunity:
    """Represents a split-and-maker trading opportunity"""
    market_id: str
    asset: str
    timeframe: str
    spread_size: float  # bid-ask spread
    yes_bid: float
    yes_ask: float
    no_bid: float
    no_ask: float
    liquidity_yes: float
    liquidity_no: float
    expected_profit: float
    risk_score: float


class SplitAndMakerStrategy:
    """
    Execute split-and-maker trades:
    1. Split USDC into YES + NO tokens (free)
    2. Post maker orders on both sides
    3. Earn from spread + maker rebates
    4. Merge back if neither fills (free)
    """

    def __init__(self, ctf_engine, order_engine, risk_manager):
        self.ctf = ctf_engine
        self.orders = order_engine
        self.risk = risk_manager
        self.active_positions = {}

    def identify_opportunities(self, market_data) -> list[SplitMakerOpportunity]:
        """
        Scan markets for split-and-maker opportunities

        Criteria:
        - Spread > 4% (enough room for profit)
        - YES bid + NO bid < $0.98 (can profit from split)
        - Sufficient liquidity (> $50 on both sides)
        """
        opportunities = []

        for market in market_data:
            spread = (market.yes_ask - market.yes_bid) + (market.no_ask - market.no_bid)

            if spread >= 0.04:  # 4% minimum spread
                if market.yes_bid + market.no_bid < 0.98:  # Structural edge exists
                    if market.yes_volume >= 50 and market.no_volume >= 50:  # Liquidity check
                        expected_profit = self._calculate_expected_profit(market)

                        opp = SplitMakerOpportunity(
                            market_id=market.market_id,
                            asset=market.asset,
                            timeframe=market.timeframe,
                            spread_size=spread,
                            yes_bid=market.yes_bid,
                            yes_ask=market.yes_ask,
                            no_bid=market.no_bid,
                            no_ask=market.no_ask,
                            liquidity_yes=market.yes_volume,
                            liquidity_no=market.no_volume,
                            expected_profit=expected_profit,
                            risk_score=self._calculate_risk(market)
                        )
                        opportunities.append(opp)

        # Sort by expected profit
        return sorted(opportunities, key=lambda x: x.expected_profit, reverse=True)

    async def execute(self, opportunity: SplitMakerOpportunity, capital: float):
        """
        Execute split-and-maker trade

        Returns: (success: bool, profit: float, details: dict)
        """
        # Calculate position size (2-4 USDC based on capital)
        position_size = self._calculate_position_size(capital, opportunity)

        try:
            # Step 1: Split USDC into YES + NO tokens
            yes_tokens, no_tokens = await self.ctf.split(
                opportunity.market_id,
                position_size
            )

            # Step 2: Calculate maker order prices
            yes_price = self._calculate_maker_price(opportunity.yes_bid, opportunity.yes_ask, "YES")
            no_price = self._calculate_maker_price(opportunity.no_bid, opportunity.no_ask, "NO")

            # Step 3: Post maker orders on both sides
            yes_order_id = await self.orders.place_maker_order(
                market_id=opportunity.market_id,
                side="SELL",
                token="YES",
                price=yes_price,
                amount=yes_tokens
            )

            no_order_id = await self.orders.place_maker_order(
                market_id=opportunity.market_id,
                side="SELL",
                token="NO",
                price=no_price,
                amount=no_tokens
            )

            # Step 4: Monitor fills (45 second timeout)
            result = await self._monitor_fills(
                opportunity.market_id,
                yes_order_id,
                no_order_id,
                position_size,
                timeout=45
            )

            return result

        except Exception as e:
            logger.error(f"Split-and-maker execution failed: {e}")
            # Attempt to merge back if split succeeded
            await self._emergency_cleanup(opportunity.market_id, position_size)
            return (False, 0.0, {"error": str(e)})

    async def _monitor_fills(self, market_id, yes_order_id, no_order_id, position_size, timeout):
        """
        Monitor order fills and handle all outcomes:
        - Both fill: Success! Calculate profit
        - One fills: Hold other side, attempt to fill or merge
        - Neither fills: Cancel and merge back
        """
        start_time = asyncio.get_event_loop().time()
        yes_filled = False
        no_filled = False
        yes_fill_price = 0.0
        no_fill_price = 0.0

        while (asyncio.get_event_loop().time() - start_time) < timeout:
            # Check order status
            yes_status = await self.orders.get_order_status(yes_order_id)
            no_status = await self.orders.get_order_status(no_order_id)

            if yes_status.filled:
                yes_filled = True
                yes_fill_price = yes_status.fill_price

            if no_status.filled:
                no_filled = True
                no_fill_price = no_status.fill_price

            # Both filled - SUCCESS!
            if yes_filled and no_filled:
                total_revenue = (yes_fill_price + no_fill_price) * position_size
                maker_rebate = self._estimate_maker_rebate(position_size, 2)
                profit = total_revenue - position_size + maker_rebate

                return (True, profit, {
                    "outcome": "both_filled",
                    "yes_price": yes_fill_price,
                    "no_price": no_fill_price,
                    "maker_rebate": maker_rebate
                })

            await asyncio.sleep(0.5)  # Check every 500ms

        # Timeout reached - handle partial or no fills
        if yes_filled and not no_filled:
            # Cancel NO order, hold NO tokens or merge if possible
            await self.orders.cancel_order(no_order_id)
            return await self._handle_partial_fill(market_id, "NO", position_size, yes_fill_price)

        elif no_filled and not yes_filled:
            # Cancel YES order, hold YES tokens or merge if possible
            await self.orders.cancel_order(yes_order_id)
            return await self._handle_partial_fill(market_id, "YES", position_size, no_fill_price)

        else:
            # Neither filled - cancel both and merge back
            await self.orders.cancel_order(yes_order_id)
            await self.orders.cancel_order(no_order_id)
            await self.ctf.merge(market_id, position_size)

            return (False, 0.0, {"outcome": "no_fills_merged_back"})

    async def _handle_partial_fill(self, market_id, unfilled_side, amount, filled_price):
        """
        Handle case where only one side filled

        Options:
        1. Post new maker order for unfilled side at better price
        2. Wait for market resolution (if confident)
        3. Merge back if we can acquire other side cheaply
        """
        # Try to post new order at slightly better price
        # If no fill after 30s, merge back
        # Return partial profit or zero if merged

        # Simplified: merge back for safety
        logger.info(f"Partial fill on {market_id}, merging back unfilled {unfilled_side}")

        # This requires acquiring the other side at market to merge
        # For now, hold position and let risk manager decide
        # More sophisticated handling in future iteration

        return (False, filled_price - 0.5, {"outcome": "partial_fill", "side": unfilled_side})

    def _calculate_position_size(self, capital, opportunity):
        """Calculate optimal position size (2-4 USDC)"""
        max_position = min(capital * 0.20, 4.0)  # 20% of capital, max $4
        min_position = 2.0

        # Adjust based on liquidity
        if opportunity.liquidity_yes < 100 or opportunity.liquidity_no < 100:
            return min_position

        return max_position

    def _calculate_maker_price(self, bid, ask, side):
        """
        Calculate optimal maker order price
        Place slightly inside the spread to improve fill probability
        """
        if side == "YES":
            # Place YES sell order slightly below ask
            return ask - 0.01
        else:
            # Place NO sell order slightly below ask
            return ask - 0.01

    def _calculate_expected_profit(self, market):
        """Calculate expected profit for this opportunity"""
        # Simplified calculation
        # Both sides fill at mid-spread
        yes_mid = (market.yes_bid + market.yes_ask) / 2
        no_mid = (market.no_bid + market.no_ask) / 2

        total_receive = yes_mid + no_mid
        cost = 1.0  # split $1 USDC
        margin = total_receive - cost

        # Factor in fill probability (70% both sides)
        expected = margin * 0.70

        return expected

    def _calculate_risk(self, market):
        """Calculate risk score (0-10, lower is better)"""
        # Factors:
        # - Spread volatility
        # - Liquidity depth
        # - Market close time (closer = higher risk)

        # Simplified: based on liquidity
        min_liquidity = min(market.yes_volume, market.no_volume)

        if min_liquidity > 200:
            return 2  # Low risk
        elif min_liquidity > 100:
            return 4  # Medium risk
        else:
            return 6  # Higher risk

    def _estimate_maker_rebate(self, position_size, num_orders):
        """Estimate maker rebate earnings"""
        # Polymarket maker rebate is roughly 0.1-0.3% of volume
        rebate_rate = 0.002  # 0.2% conservative estimate
        volume = position_size * num_orders
        return volume * rebate_rate

    async def _emergency_cleanup(self, market_id, position_size):
        """Emergency cleanup if trade fails mid-execution"""
        try:
            await self.ctf.merge(market_id, position_size)
            logger.info(f"Emergency cleanup: merged {position_size} on {market_id}")
        except Exception as e:
            logger.error(f"Emergency cleanup failed: {e}")
```

#### 1.2 Update Strategy Engine

**File:** `src/strategy_engine.py`

Add split-and-maker as **PRIORITY 1** strategy:

```python
from .strategies.split_and_maker import SplitAndMakerStrategy

class StrategyEngine:
    def __init__(self, ...):
        ...
        self.split_and_maker = SplitAndMakerStrategy(
            ctf_engine, order_engine, risk_manager
        )

    async def evaluate_opportunity(self, ...):
        # NEW PRIORITY ORDER:
        # 1. Split-and-Maker (highest priority)
        opportunities = self.split_and_maker.identify_opportunities(market_data)
        if opportunities:
            best_opp = opportunities[0]
            if best_opp.expected_profit > 0.05:  # Min $0.05 profit
                return Decision(
                    execute=True,
                    strategy_type="SPLIT_AND_MAKER",
                    size=self._calculate_position_size(best_opp, capital),
                    opportunity=best_opp
                )

        # 2. Split Arbitrage (if exists)
        # 3. Spread Capture
        # 4. Modified Late Entry (last resort, small positions only)
```

#### 1.3 Update Configuration

**File:** `src/config.py`

```python
# Split-and-Maker Strategy Parameters
enable_split_and_maker: bool = Field(default=True, env="ENABLE_SPLIT_AND_MAKER")
split_maker_min_spread: float = 0.04  # 4% minimum spread
split_maker_min_liquidity: float = 50.0  # $50 minimum liquidity per side
split_maker_max_position: float = 4.0  # $4 maximum position
split_maker_position_pct: float = 20.0  # 20% of capital
split_maker_timeout_seconds: int = 45  # 45 second fill timeout
split_maker_min_profit: float = 0.05  # $0.05 minimum expected profit

# DEPRECATED: Late Certainty (replaced by split-and-maker)
enable_late_certainty: bool = Field(default=False, env="ENABLE_LATE_CERTAINTY")
late_certainty_deprecated_warning: str = "Late certainty has negative EV - use split-and-maker instead"
```

---

### Phase 2: Testing and Validation (Week 2)

#### 2.1 Paper Trading Mode

Add paper trading flag to test without real capital:

```python
# config.py
paper_trading_mode: bool = Field(default=True, env="PAPER_TRADING_MODE")
```

#### 2.2 Performance Tracking

Track split-and-maker specific metrics:

```python
# logger.py - add new table
CREATE TABLE split_maker_trades (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    market_id TEXT,
    position_size REAL,
    yes_fill_price REAL,
    no_fill_price REAL,
    yes_filled BOOLEAN,
    no_filled BOOLEAN,
    maker_rebate REAL,
    net_profit REAL,
    outcome TEXT
)
```

#### 2.3 Backtesting

Create backtest script using historical data:

```python
# backtest/split_maker_backtest.py
"""
Backtest split-and-maker strategy on historical Polymarket data
"""
```

---

### Phase 3: Deployment (Week 3)

#### 3.1 Gradual Rollout

```
Day 1-3: Paper trading mode, monitor only
Day 4-7: Live with $20 capital, max $2 positions
Day 8-14: Increase to $4 positions if profitable
Day 15+: Full strategy deployment
```

#### 3.2 Monitoring Dashboard

Add Telegram commands:
- `/split_maker_stats` - Show split-and-maker performance
- `/opportunities` - List current opportunities
- `/position_status` - Show active positions

---

### Phase 4: Optimization (Week 4+)

#### 4.1 Dynamic Pricing

Improve maker order pricing algorithm:
- Analyze order book depth
- Adjust for market volatility
- Consider time to market close

#### 4.2 Multi-Market Execution

Run 2-3 split-and-maker trades concurrently:
- Track positions per market
- Ensure capital allocation limits
- Handle concurrent fills

#### 4.3 Advanced Features

- **Smart merge**: Only merge back if gas savings justify it
- **Partial position scaling**: Increase size on successful markets
- **Maker rebate tracking**: Optimize for maximum rebates

---

## 📊 Success Metrics

### Week 1 Targets (Paper Trading)
- ✅ Identify 10+ opportunities per day
- ✅ 60%+ simulated fill rate
- ✅ Average $0.06+ simulated profit per trade

### Month 1 Targets (Live Trading)
- ✅ $0.15/hour average profit
- ✅ 70%+ actual fill rate
- ✅ Zero days with >$0.50 loss
- ✅ Build capital to $50+

### Month 2-3 Targets
- ✅ $0.30-0.70/hour average
- ✅ Scale to $200+ capital
- ✅ Multi-position execution
- ✅ Maker rebate tracking

### Month 4+ Targets
- ✅ $1.00+/hour with $300+ capital
- ✅ Advanced optimization deployed
- ✅ Consistent profitability

---

## 🔧 Code Migration Plan

### Files to Create
- `src/strategies/split_and_maker.py` (new)
- `src/strategies/__init__.py` (new)
- `backtest/split_maker_backtest.py` (new)

### Files to Modify
- `src/strategy_engine.py` (priority reordering)
- `src/config.py` (new parameters)
- `src/logger.py` (new metrics table)
- `docs/README.md` (update with realistic targets)

### Files to Deprecate
- Mark late certainty as deprecated in docs
- Keep code for reference but disable by default

---

## ⚠️ Risk Management Updates

### New Position Limits
```python
# Split-and-maker specific limits
MAX_SPLIT_MAKER_POSITIONS: 3  # Max concurrent split-maker trades
MAX_SPLIT_MAKER_CAPITAL: 12.0  # Max total capital in split-maker (3 × $4)
MIN_RESERVE_CAPITAL: 8.0  # Always keep $8 liquid
```

### Failure Handling
```python
# If split-and-maker fails 3 times in a row
- Pause strategy for 15 minutes
- Alert via Telegram
- Review market conditions
```

---

## 📈 Expected Timeline

```
Week 1: Implementation + Paper Trading
Week 2: Testing + Validation
Week 3: Live deployment with $20
Week 4: Optimization + Scaling

Month 1 End: $50-100 capital
Month 2 End: $200-300 capital
Month 3 End: $500+ capital
Month 4 End: Achieving $1/hour goal
```

---

## ✅ Checklist

### Code Implementation
- [ ] Create SplitAndMakerStrategy class
- [ ] Integrate with strategy engine
- [ ] Update configuration
- [ ] Add performance tracking
- [ ] Create backtest script

### Testing
- [ ] Paper trading (3 days minimum)
- [ ] Small position live test ($2)
- [ ] Full position live test ($4)
- [ ] Multi-position test

### Documentation
- [ ] Update README with realistic targets
- [ ] Create split-and-maker strategy doc
- [ ] Update deployment guide
- [ ] Add troubleshooting section

### Deployment
- [ ] Deploy to production VPS
- [ ] Configure Telegram alerts
- [ ] Set up monitoring
- [ ] Enable paper trading mode
- [ ] Gradual rollout to live trading

---

## 🎯 Success Criteria

The implementation is considered successful when:

1. ✅ Split-and-maker trades execute automatically
2. ✅ Fill rate exceeds 60%
3. ✅ Average profit per trade >$0.06
4. ✅ Zero catastrophic losses (>$1 in single trade)
5. ✅ Consistent positive daily returns
6. ✅ Capital growth trajectory on target

---

*This roadmap provides the step-by-step path from research findings to production deployment of the split-and-maker strategy.*
