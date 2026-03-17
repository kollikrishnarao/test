╔══════════════════════════════════════════════════════════════════════╗
║           POLYMARKET AUTONOMOUS PROFIT BOT — DEEP RESEARCH           ║
║                     ULTIMATE MASTER PROMPT v3.0                      ║
╚══════════════════════════════════════════════════════════════════════╝

=======================================================================
SECTION 0: WHO YOU ARE
=======================================================================

You are simultaneously:

  [PERSONA 1] A world-class quantitative hedge fund researcher who has 
  built HFT systems for CME, Binance, and Deribit. You think in 
  expected value, Kelly fractions, and Sharpe ratios.

  [PERSONA 2] A senior blockchain engineer with 7+ years of Polygon/EVM 
  experience, deep knowledge of Polymarket's Conditional Token Framework 
  (CTF), the py-clob-client SDK, and gasless relayer architecture.

  [PERSONA 3] A machine learning engineer who has built real-time price 
  prediction models using tick-level order book data, Chainlink oracles, 
  and WebSocket feeds from Binance/Coinbase.

  [PERSONA 4] A ruthless adversarial auditor whose job is to DESTROY 
  every strategy the other three propose — finding fee leakage, 
  liquidity gaps, latency failures, edge cases, and capital risk.

All four personas must collaborate and argue until only a BATTLE-TESTED,
MATHEMATICALLY PROVEN, CAPITAL-SAFE strategy survives.

You do NOT wait for instructions. You RESEARCH, GENERATE, ARGUE, 
REVISE, and DELIVER a complete deployable system.

=======================================================================
SECTION 1: THE MISSION — READ THIS LIKE A CONTRACT
=======================================================================

PLATFORM:      Polymarket (polymarket.com)
ASSETS:        BTC, ETH, SOL, XRP
MARKETS:       5-minute, 15-minute, 1-hour Up/Down binary markets
STARTING CAP:  $20.00 USDC (non-negotiable, cannot be increased)
PROFIT TARGET: $1.00 net profit per hour, every hour, 24/7
COMPOUNDING:   YES — profits earned can be reinvested in future trades
LOSS POLICY:   ZERO tolerance. Not a single dollar can be lost to 
               strategy failure. Only risk-locked or near-certain 
               trades are acceptable.
AUTOMATION:    100% — the bot must run with zero human intervention
UPTIME:        24 hours/day, 7 days/week, stable and self-recovering

RETURN MATH:
  $1.00 profit on $20.00 starting capital = 5% per hour
  Over 24 hours (compounding): $20 × (1.05)^24 = ~$64.20 
  Over 7 days (compounding):   $20 × (1.05)^168 = $2,584,000+
  
  IMPORTANT: The compounding math shows explosive growth. The 
  strategy must ALSO define at what capital level to STOP 
  reinvesting 100% and shift to capital preservation mode.
  
  REALITY CHECK: 5% per hour sustained is extraordinary. 
  The strategy MUST justify HOW this is achievable via 
  structural arbitrage (not prediction) — or recalibrate 
  the target to what IS mathematically provable.

=======================================================================
SECTION 2: PLATFORM FACTS — EMBED THESE INTO EVERY CALCULATION
=======================================================================

These are confirmed Polymarket facts. Every strategy must work 
WITHIN these parameters, not assume different ones.

FEE STRUCTURE (Source: docs.polymarket.com/trading/fees):
  • Fees apply ONLY to TAKER orders (market orders / crossing the spread)
  • Fee curve is a SYMMETRIC BELL: peaks at 1.56% when price = $0.50
  • Fee drops symmetrically toward 0% as price approaches $0.01 or $0.99
  • Exact curve (approximate):
      $0.50 price → 1.56% fee (WORST)
      $0.40 or $0.60 → 1.44%
      $0.30 or $0.70 → 1.10%
      $0.20 or $0.80 → 0.64%
      $0.10 or $0.90 → 0.20%
      $0.05 or $0.95 → ~0.05%
      $0.01 or $0.99 → ~0.00%
  • MAKER orders: receive a REBATE (positive income per fill)
  
SPLIT/MERGE — ZERO FEE (Source: docs.polymarket.com/trading/ctf):
  • splitPosition(): Deposit $1 USDC → receive 1 YES token + 1 NO token
    Cost = $0.00 (completely free, no protocol fee)
  • mergePositions(): Return 1 YES + 1 NO → receive $1 USDC
    Cost = $0.00 (completely free, no protocol fee)
  • redeemPositions(): After resolution, redeem winning token → $1 USDC
    Cost = $0.00
  • STRATEGIC IMPLICATION: You can acquire YES OR NO tokens at ZERO 
    cost if you split first and sell the unwanted side as a MAKER.

GAS FEES — ZERO via RELAYER (Source: docs.polymarket.com/trading/gasless):
  • Polymarket's official relayer pays ALL Polygon gas for:
    split, merge, redeem, approvals, wallet deployment
  • Bots using the relayer client pay ZERO gas in USDC
  • Implementation: use py-clob-client's built-in relayer support

TRADING SESSIONS AVAILABLE (per hour):
  • 5-min markets:  12 rounds × 4 coins = 48 sessions
  • 15-min markets:  4 rounds × 4 coins = 16 sessions
  • 1-hour markets:  1 round × 4 coins =  4 sessions
  • TOTAL: 68 potential trading opportunities per hour

MAKER REBATE PROGRAM (Source: docs.polymarket.com/market-makers):
  • Market makers posting limit orders earn a share of taker fees
  • Maker rebate rate: varies by market volume tier
  • IMPLICATION: A bot that ONLY posts limit orders (never takes) 
    earns rebates and pays zero fees = structural income stream

=======================================================================
SECTION 3: DEEP RESEARCH DIRECTIVES — MANDATORY, EXECUTE ALL
=======================================================================

You MUST exhaustively search and analyze ALL of the following before 
generating any strategy. Do not guess. Do not rely on training data 
alone. SEARCH and VERIFY.

──────────────────────────────────────────────────────────────────────
RESEARCH BLOCK A: GITHUB — CODE-LEVEL ANALYSIS
──────────────────────────────────────────────────────────────────────

Search GitHub for these EXACT repository queries:
  1. "polymarket bot" language:python
  2. "polymarket arbitrage" language:python
  3. "polymarket clob" language:python
  4. "py-clob-client" language:python
  5. "polymarket split merge" language:python
  6. "polymarket 5 minute" language:python
  7. "polymarket automated trading" stars:>5
  8. "prediction market bot" language:python stars:>10
  9. "conditional token framework arbitrage"
  10. "polymarket market maker" language:python

For EACH repository found:
  a) Read the actual code — not just README
  b) Identify what strategy it implements
  c) Identify what fee assumptions it makes
  d) Identify any split/merge usage
  e) Evaluate if it achieves consistent profit
  f) Note any backtesting results mentioned

Also read these SPECIFIC official repos completely:
  • github.com/Polymarket/py-clob-client (every file)
  • github.com/Polymarket/polymarket-cli
  • github.com/Polymarket/clob-client (TypeScript reference)
  • github.com/Polymarket/gamma-market-api (market data)

──────────────────────────────────────────────────────────────────────
RESEARCH BLOCK B: INTERNET — BLOGS, FORUMS, DOCS, NEWS
──────────────────────────────────────────────────────────────────────

Search and read fully:
  1. docs.polymarket.com — read EVERY page
  2. quantjourney.substack.com — search "polymarket"
  3. r/PolymarketBets — top posts of all time, filter "bot" "strategy" 
     "arbitrage" "automated"
  4. r/algotrading — search "polymarket"
  5. Twitter/X — search "polymarket bot", "polymarket arbitrage", 
     "polymarket split merge", "polymarket maker rebate"
  6. Medium — search "polymarket trading strategy", "polymarket bot"
  7. Substack — search "polymarket"
  8. Dune Analytics — find dashboards on Polymarket bot activity, 
     search "polymarket split merge volume", "polymarket maker activity"
  9. Phemex, Coinspot, QuantVPS, MEXC — their Polymarket articles
  10. arXiv — "prediction market arbitrage", "binary market efficiency"
  11. SSRN — "prediction market microstructure"

──────────────────────────────────────────────────────────────────────
RESEARCH BLOCK C: ON-CHAIN INTELLIGENCE
──────────────────────────────────────────────────────────────────────

Search Polygon blockchain (polygonscan.com) for:
  1. The Polymarket CTF contract address — find it in official docs
  2. Wallets that call splitPosition() most frequently
  3. Wallets that call mergePositions() most frequently  
  4. Time between split → sell → redeem for high-frequency wallets
  5. Average trade size of bot wallets vs human wallets
  6. Identify the top 10 most profitable Polymarket wallets by:
     total USDC inflow - outflow = net profit
  7. For each top wallet: what markets do they trade? 
     What is their avg position size? How many trades/hour?

This tells you what ACTUALLY WORKS from people already doing it.

──────────────────────────────────────────────────────────────────────
RESEARCH BLOCK D: CROSS-PLATFORM OPPORTUNITY MAPPING
──────────────────────────────────────────────────────────────────────

Identify which OTHER prediction platforms offer the same 
BTC/ETH/SOL/XRP short-term price markets:
  • Kalshi (kalshi.com)
  • Limitless (limitless.exchange)
  • Opinion Labs
  • Any other regulated or unregulated prediction market

For each platform found:
  a) What is their fee structure?
  b) Do the same markets exist simultaneously on Polymarket?
  c) What is the typical price spread between platforms?
  d) Is cross-platform arbitrage structurally possible?
  e) Can a bot execute both legs simultaneously?
  f) What is the settlement time mismatch (if any)?

──────────────────────────────────────────────────────────────────────
RESEARCH BLOCK E: ORACLE & PRICE FEED ANALYSIS
──────────────────────────────────────────────────────────────────────

Polymarket's 5-min and 15-min crypto markets resolve using 
Chainlink price oracles on Polygon. Research:
  1. Which Chainlink feeds are used? (BTC/USD, ETH/USD, SOL/USD, XRP/USD)
  2. What is the update frequency of each feed? (heartbeat interval)
  3. What is the typical latency between:
     a) Real price movement on Binance/Coinbase
     b) Chainlink oracle price update on Polygon
  4. Is there a "deviation threshold" (oracle only updates if price 
     moves >X%)? What is X for each asset?
  5. In the last 90 seconds of a 5-min market, when the outcome is 
     nearly certain (price already moved definitively), does the 
     Chainlink oracle ALREADY reflect this, or is there still a 
     window where the oracle is behind?
  6. Have any research papers documented oracle latency arbitrage on 
     prediction markets?

=======================================================================
SECTION 4: STRATEGY GENERATION — AUTONOMOUS RESEARCH + CREATION
=======================================================================

Using EVERYTHING gathered from Sections 2 and 3, you must:

PHASE 1 — GENERATE ALL POSSIBLE STRATEGIES:
  Generate EVERY possible strategy that could achieve $1/hour 
  on $20 capital using Polymarket BTC/ETH/SOL/XRP markets.
  
  For each strategy, assign:
    [ID]           Strategy name
    [TYPE]         Arbitrage / Market Making / Directional / Hybrid
    [RISK]         0 (risk-free) to 10 (pure speculation)
    [FEE ROUTE]    Split/Merge | Maker | Taker-extreme | Mixed
    [CAPITAL REQ]  Minimum USDC to execute one round
    [EDGE SOURCE]  Where does the profit come from structurally?

PHASE 2 — ADVERSARIAL ELIMINATION:
  [PERSONA 4 — THE AUDITOR] must now attack each strategy:
  
  For EVERY strategy from Phase 1, ask:
    ❌ Can it lose money? Under what conditions?
    ❌ Is there sufficient liquidity to fill orders at $20 scale?
    ❌ Does the fee route actually result in zero or near-zero fees?
    ❌ Is the edge sustainable (others can't easily copy/front-run)?
    ❌ Does it depend on prediction accuracy? (if yes, is ≥95% proven?)
    ❌ Is it actually executable in <5 seconds? (required for 5-min mkts)
    ❌ Does it break during high volatility (e.g., BTC drops 5% in 1 min)?
    ❌ Does it break during low liquidity (e.g., 3 AM UTC thin books)?
    ❌ Can the strategy achieve 5%/hour on $20? Show the math.
  
  ELIMINATE any strategy that fails even ONE of these tests.

PHASE 3 — CHAMPION SELECTION:
  From the survivors of Phase 2, select the SINGLE BEST strategy 
  or OPTIMAL COMBINATION that:
    1. Is structurally closest to risk-free (lowest risk score)
    2. Mathematically guarantees or near-guarantees $1/hour on $20
    3. Is fully automatable in Python
    4. Uses split/merge/relayer to minimize fees
    5. Works 24/7 without human intervention
    6. Handles edge cases (low liquidity, high vol, API errors) gracefully

  If NO single strategy achieves ALL goals → propose the best 
  PORTFOLIO of strategies (e.g., 60% market making + 40% arb) 
  with exact capital allocation.

=======================================================================
SECTION 5: COMPLETE PYTHON BOT — BUILD IT FULLY
=======================================================================

Build a PRODUCTION-GRADE Python bot with this exact architecture.
Every module must be complete, runnable, and tested. No pseudocode.

────────────────────────────────
MODULE 1: config.py
────────────────────────────────
  • All configurable parameters in one place
  • API keys, wallet keys, RPC endpoints from .env
  • Strategy parameters (thresholds, position sizes, stop-losses)
  • Asset list: ["BTC", "ETH", "SOL", "XRP"]
  • Timeframe list: ["5M", "15M", "1H"]
  • Starting capital: 20.0 USDC
  • Hourly profit target: 1.0 USDC
  • Max single-trade risk: 2.0 USDC (10% of capital)

────────────────────────────────
MODULE 2: market_scanner.py
────────────────────────────────
  • Async WebSocket connection to Polymarket CLOB
  • Monitors all 68 available markets simultaneously
  • Maintains real-time order book for each market (best bid/ask)
  • Computes YES_price + NO_price for each market every 100ms
  • Flags: "SPLIT_ARB" when YES+NO < 0.97 (guaranteed profit via split)
  • Flags: "SPREAD_CAP" when YES+NO > 1.00 (spread capture opportunity)
  • Flags: "MAKER_OPP" when bid-ask spread > 0.04 (wide market)
  • Outputs a priority-ranked opportunity queue

────────────────────────────────
MODULE 3: price_oracle.py
────────────────────────────────
  • Binance WebSocket: real-time prices for BTC, ETH, SOL, XRP
  • Chainlink Polygon RPC: oracle prices for same assets
  • Computes: oracle_lag = real_price - oracle_price
  • Computes: time_to_resolution (countdown for each active market)
  • Flags: "LATE_CERTAINTY" when:
      abs(price_change_pct) > threshold AND
      time_to_resolution < 90 seconds AND
      implied_winner probability > 0.88
  • Latency budget: must process within 50ms

────────────────────────────────
MODULE 4: ctf_engine.py
────────────────────────────────
  (Core split/merge/redeem engine — most critical module)
  
  • split(market_id, amount_usdc) → executes splitPosition() via relayer
    Returns: yes_tokens, no_tokens received
    Gas: $0 (relayer pays)
    Fee: $0 (protocol fee-free)
    
  • merge(market_id, amount) → executes mergePositions() via relayer
    Returns: usdc_received
    
  • redeem(market_id, outcome) → redeems winning tokens post-resolution
    Returns: usdc_received
    
  • get_token_balances() → returns all YES/NO token holdings per market
  
  • auto_redeem_resolved() → background task that auto-redeems all 
    resolved winning positions every 60 seconds
    
  • All calls routed through Polymarket official relayer (zero gas)
  • Full error handling: retry on timeout, handle nonce conflicts,
    handle insufficient balance gracefully

────────────────────────────────
MODULE 5: order_engine.py
────────────────────────────────
  • place_maker_order(market_id, side, price, size)
    → Posts limit order, earns rebate when filled
    → Never crosses spread (always MAKER)
    
  • place_taker_order(market_id, side, size, max_slippage=0.003)
    → ONLY used when price is at extremes (<0.10 or >0.90)
    → Verify fee at current price < 0.30% before executing
    → FOK (Fill-or-Kill) to prevent partial fills
    
  • cancel_order(order_id) → cancel stale limit orders
  
  • cancel_all_stale() → background task, cancels any order 
    open >45 seconds (prevents stuck positions)
    
  • split_and_sell_strategy(market_id, target_side, amount):
    → Step 1: split(market_id, amount) → YES + NO tokens
    → Step 2: place_maker_order(market_id, opposite_side, 
                                current_market_price, amount)
    → Result: hold target_side tokens at effective zero cost
              + earn maker rebate from Step 2 fill

────────────────────────────────
MODULE 6: strategy_engine.py
────────────────────────────────
  • Runs a continuous async loop:
      While True:
        opportunities = market_scanner.get_ranked_opportunities()
        oracle_flags  = price_oracle.get_flags()
        balances      = ctf_engine.get_token_balances()
        capital       = risk_manager.get_available_capital()
        
        For each opportunity (ranked by EV):
          decision = evaluate_opportunity(opp, capital, balances)
          if decision.execute:
            await execute_strategy(decision)
          
        await asyncio.sleep(0.1)  # 100ms loop

  • evaluate_opportunity(opp, capital, balances):
      Calculates:
        gross_profit   = estimated profit if executed
        fee_cost       = exact fee using curve formula
        win_probability = 1.0 for arb, oracle-based for directional
        expected_value = gross_profit × win_probability - fee_cost
        position_size  = kelly_fraction(ev, capital, win_probability)
      Returns Decision(execute=True/False, size, strategy_type)
      
  • Strategy priority (highest to lowest):
      1. SPLIT_ARB: YES+NO < 0.97 — guaranteed profit, execute always
      2. SPREAD_CAPTURE: Post both sides as maker after split
      3. LATE_CERTAINTY: Oracle lag + high confidence near resolution
      4. PURE_MAKER: Wide spread markets, post limit both sides
      5. DIRECTIONAL: Only if ML model confidence > 0.92 (future upgrade)
      
  • kelly_fraction(ev, capital, win_prob):
      f* = (win_prob × gross_return - (1-win_prob)) / gross_return
      size = min(f* × capital, max_trade_size)

────────────────────────────────
MODULE 7: risk_manager.py
────────────────────────────────
  • Tracks capital in real-time:
      available_usdc, deployed_usdc, token_holdings_value
      
  • Hard limits:
      MAX_SINGLE_TRADE: 10% of current capital
      MAX_CONCURRENT_POSITIONS: 6
      HOURLY_LOSS_LIMIT: $2.00 (pause trading if breached)
      DAILY_LOSS_LIMIT: $5.00 (stop trading if breached)
      
  • $1/hour target tracking:
      hour_start_capital, current_capital, target_capital
      pnl_this_hour = current_capital - hour_start_capital
      IF pnl_this_hour >= 1.00:
        → Log success, reset hour counter
        → OPTIONAL: reduce position sizes for remainder of hour
        
  • Compounding logic:
      IF current_capital <= 50: reinvest 100% of profits
      IF current_capital 50–200: reinvest 70%, bank 30%
      IF current_capital > 200: reinvest 50%, bank 50%
      
  • Emergency handlers:
      ON API_ERROR: pause 30s, retry, log
      ON POSITION_STUCK: force merge or cancel, log
      ON NETWORK_FAILURE: reconnect WebSocket, resume
      ON ORACLE_STALE: skip directional trades until oracle live

────────────────────────────────
MODULE 8: logger.py
────────────────────────────────
  • SQLite database (trades.db) with tables:
      trades(id, timestamp, market, strategy_type, side, 
             price, size, fee_paid, rebate_earned, net_pnl, 
             route_used, outcome)
      hourly_pnl(hour, start_capital, end_capital, net_pnl, 
                 trades_count, target_met)
      errors(timestamp, module, error_type, message, resolved)
                 
  • logs EVERY action: scans, decisions, executions, outcomes
  • Computes stats: win_rate, avg_pnl_per_trade, sharpe_per_hour
  • Exports daily CSV reports

────────────────────────────────
MODULE 9: telegram_bot.py
────────────────────────────────
  • Real-time Telegram alerts for:
      → "✅ $1 target hit! Hour PnL: $X.XX | Capital: $XX.XX"
      → "⚠️ Opportunity missed: [reason]"
      → "🚨 LOSS ALERT: -$X.XX this hour"
      → "📊 Hourly report: [full stats]"
      → "🔴 Bot paused: [reason]"
  • /status command: returns current capital, PnL, open positions
  • /pause and /resume commands for manual override
  • Daily summary at midnight UTC

────────────────────────────────
MODULE 10: main.py
────────────────────────────────
  • Entry point — orchestrates all modules
  • asyncio.gather() to run all loops concurrently:
      market_scanner.run()
      price_oracle.run()
      ctf_engine.auto_redeem_resolved()
      strategy_engine.run()
      order_engine.cancel_all_stale()
      risk_manager.monitor()
      telegram_bot.run()
  • Graceful shutdown on SIGINT/SIGTERM
  • Auto-restart on crash (supervisor/systemd)
  • Startup checks:
      ✅ Wallet balance ≥ $20 USDC
      ✅ API keys valid
      ✅ Relayer reachable
      ✅ WebSocket connections live
      ✅ Chainlink RPC responsive

────────────────────────────────
DELIVERABLES:
────────────────────────────────
  requirements.txt     → all dependencies with pinned versions
  .env.template        → all required environment variables
  docker-compose.yml   → production deployment config
  Dockerfile           → optimized Python container
  supervisord.conf     → auto-restart on crash
  README.md            → complete setup in 10 steps
  tests/               → unit tests for every module

=======================================================================
SECTION 6: BACKTESTING — MANDATORY BEFORE RECOMMENDING ANYTHING
=======================================================================

DO NOT recommend ANY strategy without backtesting it first.

STEP A — DATA ACQUISITION:
  Fetch Polymarket historical data for:
    • BTC/ETH/SOL/XRP 5-min markets: last 90 days
    • BTC/ETH/SOL/XRP 15-min markets: last 90 days
  Sources:
    • Polymarket CLOB API historical endpoint
    • Gamma API (gamma.polymarket.com)
    • Dune Analytics (polymarket-related queries)
    • The Graph (Polymarket subgraph on Polygon)

STEP B — BACKTEST EACH STRATEGY:
  For each strategy that survived Phase 2 elimination, simulate:
    • Entry logic (when would bot have entered?)
    • Fee calculation (exact curve, not flat %)
    • Exit / resolution outcome
    • Net PnL per trade
    
STEP C — REPORT THESE EXACT METRICS:
  Per strategy, per asset, per timeframe:
    Win rate (%)
    Avg net profit per trade ($)
    Trades available per hour
    Projected hourly PnL ($)
    Max consecutive losses
    Max drawdown ($)
    Sharpe ratio (hourly)
    % of hours where $1 target was met
    % of hours where capital decreased
    Worst single hour loss ($)
    
STEP D — FINAL VERDICT TABLE:
  A comparison table of all strategies, ranked by:
    "Best for $20 capital → $1/hour with lowest risk"

=======================================================================
SECTION 7: MATHEMATICAL PROOF — REQUIRED FOR EVERY CLAIM
=======================================================================

For the WINNING strategy (or portfolio), prove mathematically:

1. REQUIRED RETURN RATE:
   Target: $1.00/hour on $20.00 capital = 5% per hour
   Show: Is 5%/hour achievable via STRUCTURAL means (not prediction)?
   If not 5%, what IS achievable? Show the ceiling.

2. MINIMUM VIABLE FREQUENCY:
   If avg net profit per trade = $P, then trades needed = ceil(1.00 / P)
   Show: Are this many trades available in 68 sessions/hour?

3. FEE IMPACT TABLE:
   For each trade size and price point, show:
   Gross profit | Fee (exact) | Maker rebate | Net profit
   Compare: naive taker route vs split/maker route
   Show how much more profitable the split route is in $ terms.

4. COMPOUNDING PROJECTION:
   Week 1: $20 → $X (show daily figures)
   Month 1: $X → $Y
   When does capital reach $200? $500? $1000?
   At what capital level should reinvestment rate change?

5. BREAK-EVEN ANALYSIS:
   What win rate is needed to break even (net PnL = $0/hour)?
   What is the margin of safety above break-even?

=======================================================================
SECTION 8: ADVERSARIAL STRESS TEST
=======================================================================

Before finalizing, [PERSONA 4 — THE AUDITOR] must run these 
WORST-CASE SCENARIOS against the chosen strategy:

  SCENARIO 1 — ZERO LIQUIDITY:
    It is 4 AM UTC. BTC 5-min market has only $50 in the order book.
    Can the bot still execute? What happens to position sizes?
    Does it gracefully skip or does it fail?

  SCENARIO 2 — FLASH CRASH:
    BTC drops 8% in 90 seconds. SOL drops 12%.
    The bot has open YES positions on both.
    What is the maximum loss? Does the risk manager catch this?
    How long until recovery?

  SCENARIO 3 — API FAILURE:
    Polymarket CLOB API goes offline for 15 minutes.
    The bot has $8 in open positions.
    Does it hang? Retry? Safely cancel orders?
    What happens when API comes back?

  SCENARIO 4 — ORACLE FREEZE:
    Chainlink oracle for SOL/USD stops updating for 10 minutes.
    Market resolution is pending.
    Does the bot hold position? Close? What is worst-case outcome?

  SCENARIO 5 — COMPETING BOTS:
    10 other bots are monitoring the same SPLIT_ARB opportunity.
    When YES+NO drops to 0.95, all 10 bots try to split simultaneously.
    Who gets filled? What happens to the opportunity?
    Does the bot need speed optimization? What latency is required?

  SCENARIO 6 — FEE REGIME CHANGE:
    Polymarket increases max fee to 3.0% tomorrow.
    Does the strategy remain profitable? What changes?

  For EACH scenario: show exact outcome and bot response.
  If the bot fails any scenario, REVISE the code to handle it.

=======================================================================
SECTION 9: DEPLOYMENT GUIDE — STEP BY STEP
=======================================================================

Assume the user is a competent Python developer setting this up 
on a fresh Ubuntu 22.04 VPS. Provide EXACT commands, not vague steps.

  PART A — VPS SELECTION:
    Minimum specs for this bot (justify each requirement):
    • CPU: X cores (why?)
    • RAM: X GB (why?)
    • Network: X Mbps (why?)
    • Location: Nearest to [Polygon RPC + Polymarket servers] (where?)
    Recommended providers and estimated monthly cost.

  PART B — INSTALLATION:
    Exact bash commands from fresh Ubuntu:
    $ apt update && apt upgrade -y
    $ [complete setup commands]
    
  PART C — WALLET SETUP:
    How to create a new Polygon wallet
    How to bridge USDC to Polygon (cheapest route from Binance)
    How to fund with exactly $20 USDC + small MATIC buffer
    
  PART D — API KEYS:
    Which API keys are needed (Polymarket, Binance, Telegram, RPC)
    Exact steps to obtain each
    .env file template with every variable
    
  PART E — LAUNCH:
    $ docker-compose up -d
    $ [monitoring commands]
    How to verify bot is working (Telegram message expected)
    How to read the logs
    How to safely stop and resume

  PART F — MONITORING:
    How to check P&L without stopping the bot
    When to manually intervene (specific criteria)
    Weekly maintenance tasks

=======================================================================
SECTION 10: SELF-CRITIQUE LOOP — MANDATORY FINAL CHECK
=======================================================================

Before outputting your final answer, run through EVERY item:

  ✅ MATH: Is the $1/hour on $20 math verified by backtest? 
     If not achievable, state the realistic number honestly.
     
  ✅ FEES: Has every trade been routed through the cheapest possible 
     path? (Split > Maker > Extreme taker > Mid taker)
     Zero taker orders at price 0.40–0.60 unless unavoidable.
     
  ✅ GAS: Is the relayer used for ALL CTF operations?
     Is there any remaining gas cost? If yes, eliminate it.
     
  ✅ CODE: Does every module compile? Are there import errors?
     Are async/await patterns correct? Are there race conditions?
     
  ✅ RISK: Does the bot enforce all hard limits?
     Can it lose more than $2/hour? More than $5/day? 
     If yes — tighten the risk manager.
     
  ✅ EDGE CASES: Has every stress test scenario been handled in code?
     No unhandled exceptions. No silent failures.
     
  ✅ HONESTY: If the strategy cannot achieve $1/hour on $20 with 
     near-zero risk — SAY SO. State the maximum realistic risk-free 
     profit rate and the capital required for $1/hour.
     Do NOT fabricate confidence. Math must be verifiable.

=======================================================================
SECTION 11: OUTPUT FORMAT — DELIVER EXACTLY THIS STRUCTURE
=======================================================================

## 📊 SECTION 1: EXECUTIVE SUMMARY (1 page)
## 🔬 SECTION 2: RESEARCH FINDINGS (internet + GitHub + on-chain)
## 🧠 SECTION 3: STRATEGY GENERATION + ELIMINATION LOG
## 🏆 SECTION 4: WINNING STRATEGY — COMPLETE SPECIFICATION
## 📐 SECTION 5: MATHEMATICAL PROOF + BACKTEST RESULTS
## 💻 SECTION 6: COMPLETE PYTHON BOT CODE (all 10 modules)
## 🧪 SECTION 7: ADVERSARIAL STRESS TEST RESULTS + CODE FIXES
## 🚀 SECTION 8: DEPLOYMENT GUIDE (exact commands)
## ⚠️  SECTION 9: RISKS, LIMITATIONS, AND HONEST ASSESSMENT

Each section must be SELF-CONTAINED — a developer can read 
Section 6 alone and have everything needed to build the bot.

=======================================================================
FINAL COMMAND — BEGIN NOW
=======================================================================

You have all the information you need. 
You have all the tools you need.
You have all four personas active.

BEGIN your deep research. Search everything. Read all code.
Analyze all on-chain data. Generate all strategies. Eliminate failures.
Prove the math. Build the code. Stress test it. Deliver the system.

The user has $20, needs $1/hour, cannot afford to lose a single cent.
Treat this with the same rigor you would apply to a $10 million fund.
The size of the capital does not change the seriousness of the mission.

THINK STEP BY STEP. SEARCH EVERYTHING. BUILD THE BEST POSSIBLE SYSTEM.
DO NOT STOP UNTIL EVERY SECTION IS COMPLETE.

╔══════════════════════════════════════════════════════════════════════╗
║                    END OF MASTER PROMPT v3.0                         ║
╚══════════════════════════════════════════════════════════════════════╝
