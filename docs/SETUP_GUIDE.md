# Polymarket Autonomous Trading Bot

## ⚠️ IMPORTANT DISCLAIMER

**This is an educational and research project. Trading cryptocurrency prediction markets carries significant financial risk.**

- **No Guarantees**: The strategies described in this bot are theoretical and have not been proven to generate consistent profits in live markets.
- **Financial Risk**: You can lose all of your invested capital. Only trade with money you can afford to lose completely.
- **Not Financial Advice**: This software is provided for educational purposes only and should not be considered financial advice.
- **Regulatory Compliance**: Ensure you comply with all applicable laws and regulations in your jurisdiction before using this bot.
- **Security**: Protect your private keys and never share them. This bot requires access to your wallet.

**USE AT YOUR OWN RISK.**

---

## Overview

This is a fully autonomous trading bot for Polymarket's short-term crypto prediction markets (BTC, ETH, SOL, XRP). The bot implements multiple strategies:

- **Split Arbitrage**: Exploits mispricing when YES+NO < $1.00
- **Spread Capture**: Earns from wide bid-ask spreads
- **Market Making**: Posts liquidity to earn maker rebates
- **Oracle Lag Trading**: Capitalizes on Chainlink oracle latency (when enabled)

### Key Features

- ✅ Zero-gas operations via Polymarket's relayer
- ✅ Minimized fees through split/merge and maker orders
- ✅ Comprehensive risk management and capital protection
- ✅ Real-time Telegram notifications
- ✅ SQLite database for trade tracking
- ✅ Docker deployment ready
- ✅ Auto-recovery from errors

---

## Architecture

```
src/
├── config.py           # Configuration and parameters
├── logger.py           # Database and logging
├── ctf_engine.py       # Split/merge/redeem operations
├── order_engine.py     # Order placement and management
├── market_scanner.py   # Real-time market monitoring
├── price_oracle.py     # Binance + Chainlink price feeds
├── strategy_engine.py  # Strategy evaluation and execution
├── risk_manager.py     # Capital and risk management
├── telegram_bot.py     # Notifications and commands
└── main.py             # Main orchestrator
```

---

## Quick Start

### 1. Prerequisites

- Python 3.9+
- Docker (optional, for containerized deployment)
- Polygon wallet with USDC
- Polymarket account
- Telegram bot (optional, for notifications)

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/kollikrishnarao/test.git
cd test

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.template .env

# Edit .env with your credentials
nano .env
```

Required configuration:
- `POLYMARKET_PRIVATE_KEY`: Your Polygon wallet private key
- `POLYGON_RPC_URL`: Polygon RPC endpoint (e.g., Alchemy, Infura)
- `BINANCE_API_KEY` & `BINANCE_API_SECRET`: For real-time prices
- `TELEGRAM_BOT_TOKEN` & `TELEGRAM_CHAT_ID`: For notifications (optional)

### 4. Run the Bot

**Option A: Direct Python**
```bash
python -m src.main
```

**Option B: Docker**
```bash
docker-compose up -d
```

**Option C: With Supervisor (auto-restart on crash)**
```bash
supervisord -c supervisord.conf
```

---

## Configuration Parameters

### Trading Parameters

- `STARTING_CAPITAL`: Initial USDC amount (default: 20.0)
- `HOURLY_PROFIT_TARGET`: Target profit per hour (default: 1.0)
- `MAX_SINGLE_TRADE_PERCENT`: Max % of capital per trade (default: 10)
- `MAX_CONCURRENT_POSITIONS`: Max open positions (default: 6)

### Risk Limits

- `HOURLY_LOSS_LIMIT`: Max loss per hour before pausing (default: 2.0)
- `DAILY_LOSS_LIMIT`: Max loss per day before stopping (default: 5.0)

### Strategy Toggles

- `ENABLE_SPLIT_ARB`: Enable split arbitrage (default: true)
- `ENABLE_SPREAD_CAPTURE`: Enable spread capture (default: true)
- `ENABLE_PURE_MAKER`: Enable market making (default: true)
- `ENABLE_DIRECTIONAL`: Enable directional trading (default: false)

---

## Strategy Details

### 1. Split Arbitrage (Risk-Free)

**When**: YES+NO prices sum to < $0.97

**Process**:
1. Split $1 USDC → 1 YES + 1 NO token (zero fee)
2. Sell YES at market price
3. Sell NO at market price
4. Net profit = (YES + NO) - $1.00

**Example**: YES=$0.48, NO=$0.48
- Split $10 → 10 YES + 10 NO
- Sell 10 YES @ $0.48 = $4.80
- Sell 10 NO @ $0.48 = $4.80
- Total received = $9.60 from $10 split
- Arbitrage exists if actual YES+NO < $1.00 after fees

### 2. Spread Capture

**When**: YES+NO sum > $1.00

**Process**:
1. Post maker orders on both sides
2. Earn rebates when filled
3. Close positions when profitable

### 3. Market Making

**When**: Wide bid-ask spread (> 4%)

**Process**:
1. Post limit orders on both sides of the book
2. Earn maker rebates on fills
3. Manage inventory via split/merge

---

## Risk Management

The bot enforces multiple layers of protection:

1. **Position Size Limits**: Max 10% of capital per trade
2. **Concurrent Position Limits**: Max 6 open positions
3. **Hourly Loss Limit**: Pauses trading if loss > $2/hour
4. **Daily Loss Limit**: Stops trading if loss > $5/day
5. **Kelly Criterion**: Fractional Kelly sizing for non-arbitrage trades
6. **Emergency Stop**: Manual override via Telegram

---

## Telegram Commands

- `/status`: Check bot status and current positions
- `/stats`: View trading statistics
- `/pause`: Pause trading
- `/resume`: Resume trading

---

## Monitoring

### Logs

Logs are stored in `logs/` directory:
- `bot_YYYY-MM-DD.log`: Daily log files

### Database

All trades are stored in `trades.db` SQLite database with tables:
- `trades`: Individual trade records
- `hourly_pnl`: Hourly P&L tracking
- `positions`: Open and closed positions
- `errors`: Error log
- `performance_metrics`: Performance stats

### Reports

Daily CSV reports exported to `reports/` directory.

---

## Development

### Running Tests

```bash
pytest tests/
```

### Code Structure

Each module is self-contained and can be tested independently:

```bash
# Test config
python src/config.py

# Test CTF engine
python src/ctf_engine.py

# Test order engine
python src/order_engine.py
```

---

## Deployment Guide

### VPS Requirements

**Minimum Specs**:
- CPU: 2 cores
- RAM: 2 GB
- Storage: 10 GB
- Network: 10 Mbps
- Location: Near Polygon nodes (US East recommended)

**Recommended Providers**:
- DigitalOcean ($12/month)
- AWS Lightsail ($10/month)
- Vultr ($12/month)

### Setup on Ubuntu 22.04

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y

# Clone and setup
git clone https://github.com/kollikrishnarao/test.git
cd test
cp .env.template .env
nano .env  # Configure your settings

# Run
docker-compose up -d

# View logs
docker-compose logs -f
```

---

## Wallet Setup

### 1. Create Polygon Wallet

```bash
# Using Python
from eth_account import Account
account = Account.create()
print(f"Address: {account.address}")
print(f"Private Key: {account.key.hex()}")
```

### 2. Fund with USDC

- Bridge USDC from Ethereum to Polygon via [Polygon Bridge](https://wallet.polygon.technology/bridge)
- Or buy USDC directly on Polygon via exchanges like Binance

### 3. Add Small MATIC Buffer

- Get ~$1 worth of MATIC for potential manual transactions
- Polymarket's relayer handles most gas, but backup MATIC is recommended

---

## Security Best Practices

1. **Never commit .env file** - It contains your private keys
2. **Use a dedicated wallet** - Don't use your main wallet
3. **Start with small capital** - Test with minimum amounts first
4. **Monitor regularly** - Check Telegram notifications
5. **Backup database** - Periodically backup `trades.db`
6. **Update dependencies** - Keep packages up to date

---

## Troubleshooting

### Bot won't start

- Check `.env` file is configured correctly
- Verify wallet has sufficient USDC balance
- Check `logs/` for error messages

### No trades executing

- Verify markets are active on Polymarket
- Check if risk limits are blocking trades
- Ensure API connections are working

### High fees

- Bot should primarily use maker orders (zero/negative fees)
- Check fee calculations in logs
- Verify split/merge is being used appropriately

---

## Performance Expectations

### Realistic Goals

- **Conservative**: 0.5-1% daily return
- **Moderate**: 1-3% daily return (with higher risk)
- **Aggressive**: 3-5% daily return (significant risk)

### Important Notes

- The README prompt's 5%/hour target is **extremely optimistic** and unlikely to be achievable consistently
- Real performance depends on market conditions, liquidity, and competition
- Past performance (including backtests) does not guarantee future results
- Always start with paper trading or minimum capital

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

---

## License

This project is provided as-is for educational purposes. Use at your own risk.

---

## Support

For issues and questions:
- Open an issue on GitHub
- Read the code documentation
- Check logs for error messages

---

## Acknowledgments

Built using:
- [py-clob-client](https://github.com/Polymarket/py-clob-client) - Official Polymarket Python SDK
- Polymarket Documentation
- Community research and examples

---

**Remember: Only trade with capital you can afford to lose. This bot is experimental software.**
