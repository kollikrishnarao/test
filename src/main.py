"""
Main Orchestrator
Entry point - coordinates all modules and manages lifecycle
"""
import asyncio
import signal
import sys
from loguru import logger

from .config import config
from .logger import trading_logger
from .ctf_engine import CTFEngine
from .order_engine import OrderEngine
from .market_scanner import market_scanner
from .price_oracle import price_oracle
from .strategy_engine import StrategyEngine
from .risk_manager import risk_manager
from .telegram_bot import telegram_bot


class PolymarketBot:
    """Main bot orchestrator"""

    def __init__(self):
        self.ctf_engine = CTFEngine()
        self.order_engine = OrderEngine(ctf_engine=self.ctf_engine)
        self.strategy_engine = StrategyEngine(
            ctf_engine=self.ctf_engine,
            order_engine=self.order_engine
        )
        self.running = False

    async def startup_checks(self) -> bool:
        """Perform startup checks before running"""
        logger.info("Performing startup checks...")

        # Check wallet balance
        if risk_manager.available_usdc < config.starting_capital:
            logger.error(
                f"Insufficient capital: need ${config.starting_capital}, "
                f"have ${risk_manager.available_usdc}"
            )
            return False

        # Check API keys
        if not config.polymarket_private_key:
            logger.error("Polymarket private key not configured")
            return False

        logger.success("✅ All startup checks passed")
        return True

    async def initialize_modules(self):
        """Initialize all modules"""
        logger.info("Initializing modules...")

        await self.ctf_engine.initialize()
        await self.order_engine.initialize()
        await market_scanner.initialize()
        await price_oracle.initialize()
        await self.strategy_engine.initialize()
        await telegram_bot.initialize()

        logger.success("✅ All modules initialized")

    async def start_all_tasks(self):
        """Start all background tasks"""
        logger.info("Starting background tasks...")

        # Start all async tasks
        await asyncio.gather(
            self.ctf_engine.start_auto_redeem(),
            self.order_engine.start_cancel_stale(),
            market_scanner.start_scanning(),
            price_oracle.start_updates(),
            self.strategy_engine.start_strategy(),
            risk_manager.start_monitoring(),
            telegram_bot.start(),
        )

        logger.success("✅ All background tasks started")

    async def stop_all_tasks(self):
        """Stop all background tasks"""
        logger.info("Stopping background tasks...")

        await asyncio.gather(
            self.ctf_engine.stop_auto_redeem(),
            self.order_engine.stop_cancel_stale(),
            market_scanner.stop_scanning(),
            price_oracle.stop_updates(),
            self.strategy_engine.stop_strategy(),
            risk_manager.stop_monitoring(),
            telegram_bot.stop(),
        )

        logger.info("✅ All background tasks stopped")

    async def run(self):
        """Main run loop"""
        logger.info("🚀 Starting Polymarket Autonomous Trading Bot")
        logger.info(f"Starting Capital: ${config.starting_capital}")
        logger.info(f"Hourly Target: ${config.hourly_profit_target}")
        logger.info(f"Assets: {', '.join(config.assets)}")
        logger.info(f"Timeframes: {', '.join(config.timeframes)}")

        # Startup checks
        if not await self.startup_checks():
            logger.error("❌ Startup checks failed. Exiting.")
            return

        # Initialize modules
        await self.initialize_modules()

        # Start all background tasks
        await self.start_all_tasks()

        self.running = True
        logger.success("🎯 Bot is now running. Press Ctrl+C to stop.")

        try:
            # Keep running until stopped
            while self.running:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")

        finally:
            await self.shutdown()

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down bot...")

        self.running = False

        # Stop all tasks
        await self.stop_all_tasks()

        # Final stats
        snapshot = risk_manager.get_snapshot()
        logger.info(f"Final Capital: ${snapshot.total_capital:.2f}")
        logger.info(f"Total PnL: ${snapshot.total_capital - config.starting_capital:.2f}")

        # Export final report
        trading_logger.export_daily_report()

        logger.success("✅ Bot shut down successfully")


async def main():
    """Main entry point"""
    bot = PolymarketBot()

    # Handle signals for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Signal {signum} received, initiating shutdown...")
        bot.running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception(f"Bot crashed: {e}")
        sys.exit(1)
