"""
Telegram Bot Module
Sends real-time notifications and handles commands
"""
import asyncio
from datetime import datetime
from typing import Optional
from loguru import logger

try:
    from telegram import Bot, Update
    from telegram.ext import Application, CommandHandler, ContextTypes
except ImportError:
    logger.warning("python-telegram-bot not installed")
    Bot = None
    Application = None
    CommandHandler = None

from .config import config
from .risk_manager import risk_manager, TradingStatus
from .logger import trading_logger


class TelegramBot:
    """Telegram bot for notifications and commands"""

    def __init__(self):
        self.bot: Optional[Bot] = None
        self.app: Optional[Application] = None
        self.chat_id = config.telegram_chat_id
        self._notify_task = None

    async def initialize(self):
        """Initialize Telegram bot"""
        if not config.telegram_bot_token or Bot is None:
            logger.warning("Telegram bot token not configured or library not installed")
            return

        try:
            self.app = Application.builder().token(config.telegram_bot_token).build()
            self.bot = self.app.bot

            # Register command handlers
            self.app.add_handler(CommandHandler("status", self._status_command))
            self.app.add_handler(CommandHandler("pause", self._pause_command))
            self.app.add_handler(CommandHandler("resume", self._resume_command))
            self.app.add_handler(CommandHandler("stats", self._stats_command))

            logger.info("Telegram bot initialized")
            await self.send_message("🤖 Polymarket Bot started and ready to trade!")

        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {e}")

    async def send_message(self, message: str):
        """Send a message to the configured chat"""
        if not self.bot or not self.chat_id:
            return

        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message)
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")

    async def notify_target_met(self, hour_pnl: float, capital: float):
        """Notify when hourly target is met"""
        message = (
            f"✅ $1 target hit!\n"
            f"Hour PnL: ${hour_pnl:.2f}\n"
            f"Capital: ${capital:.2f}"
        )
        await self.send_message(message)

    async def notify_opportunity_missed(self, reason: str):
        """Notify when an opportunity is missed"""
        message = f"⚠️ Opportunity missed: {reason}"
        await self.send_message(message)

    async def notify_loss_alert(self, loss: float):
        """Notify on significant loss"""
        message = f"🚨 LOSS ALERT: -${loss:.2f} this hour"
        await self.send_message(message)

    async def notify_bot_paused(self, reason: str):
        """Notify when bot is paused"""
        message = f"🔴 Bot paused: {reason}"
        await self.send_message(message)

    async def send_hourly_report(self):
        """Send hourly report"""
        stats = trading_logger.get_hourly_stats()
        snapshot = risk_manager.get_snapshot()

        message = (
            f"📊 Hourly Report\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"Trades: {stats['trades_count']}\n"
            f"PnL: ${stats['total_pnl']:.2f}\n"
            f"Avg PnL/Trade: ${stats['avg_pnl']:.2f}\n"
            f"Capital: ${snapshot.total_capital:.2f}\n"
            f"Available: ${snapshot.available_usdc:.2f}\n"
            f"Deployed: ${snapshot.deployed_usdc:.2f}"
        )
        await self.send_message(message)

    async def send_daily_summary(self):
        """Send daily summary at midnight"""
        stats = trading_logger.get_daily_stats()
        snapshot = risk_manager.get_snapshot()

        message = (
            f"📈 Daily Summary\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"Total Trades: {stats['total_trades']}\n"
            f"Win Rate: {stats['win_rate']:.1f}%\n"
            f"Total PnL: ${stats['total_pnl']:.2f}\n"
            f"Best Trade: ${stats['best_trade']:.2f}\n"
            f"Worst Trade: ${stats['worst_trade']:.2f}\n"
            f"Final Capital: ${snapshot.total_capital:.2f}"
        )
        await self.send_message(message)

    async def _status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        snapshot = risk_manager.get_snapshot()
        stats = trading_logger.get_hourly_stats()

        message = (
            f"🤖 Bot Status\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"Status: {risk_manager.status.value}\n"
            f"Capital: ${snapshot.total_capital:.2f}\n"
            f"Hour PnL: ${risk_manager.hour_pnl:.2f}\n"
            f"Day PnL: ${risk_manager.day_pnl:.2f}\n"
            f"Trades (hour): {stats['trades_count']}\n"
            f"Open Positions: {len(risk_manager.open_positions)}"
        )
        await update.message.reply_text(message)

    async def _pause_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /pause command"""
        risk_manager.pause_trading("Manual pause via Telegram")
        await update.message.reply_text("🔴 Trading paused")

    async def _resume_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /resume command"""
        risk_manager.resume_trading()
        await update.message.reply_text("✅ Trading resumed")

    async def _stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        stats = trading_logger.get_daily_stats()

        message = (
            f"📊 Statistics\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"Total Trades: {stats['total_trades']}\n"
            f"Win Rate: {stats['win_rate']:.1f}%\n"
            f"Total PnL: ${stats['total_pnl']:.2f}\n"
            f"Avg PnL: ${stats['avg_pnl']:.2f}"
        )
        await update.message.reply_text(message)

    async def run_notifications(self):
        """Background task for periodic notifications"""
        logger.info("Starting Telegram notifications")

        last_hour = datetime.now().hour
        last_day = datetime.now().day

        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                current_hour = datetime.now().hour
                current_day = datetime.now().day

                # Hourly report
                if current_hour != last_hour:
                    await self.send_hourly_report()
                    last_hour = current_hour

                # Daily summary
                if current_day != last_day:
                    await self.send_daily_summary()
                    last_day = current_day

                # Check if target met
                if risk_manager.hourly_target_met:
                    await self.notify_target_met(
                        risk_manager.hour_pnl,
                        risk_manager.total_capital
                    )

            except Exception as e:
                logger.error(f"Telegram notifications error: {e}")

    async def start(self):
        """Start the Telegram bot"""
        if self.app:
            await self.app.initialize()
            await self.app.start()
            self._notify_task = asyncio.create_task(self.run_notifications())
            logger.info("Telegram bot started")

    async def stop(self):
        """Stop the Telegram bot"""
        if self._notify_task and not self._notify_task.done():
            self._notify_task.cancel()
            try:
                await self._notify_task
            except asyncio.CancelledError:
                pass

        if self.app:
            await self.app.stop()
            await self.app.shutdown()
            logger.info("Telegram bot stopped")


# Singleton instance
telegram_bot = TelegramBot()
