"""
Logging and database module for Polymarket Trading Bot
Tracks all trades, PnL, errors, and performance metrics
"""
import asyncio
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pathlib import Path
from loguru import logger
import sys

from .config import config


class TradingLogger:
    """Handles logging and database operations"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.database_path
        self._setup_logging()
        self._init_database()

    def _setup_logging(self):
        """Configure logging"""
        logger.remove()
        logger.add(
            sys.stdout,
            colorize=True,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
            level=config.log_level,
        )
        logger.add(
            "logs/bot_{time:YYYY-MM-DD}.log",
            rotation="00:00",
            retention="30 days",
            level="DEBUG",
        )

    def _init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Trades table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                market_id TEXT NOT NULL,
                market_name TEXT,
                strategy_type TEXT NOT NULL,
                side TEXT NOT NULL,
                price REAL NOT NULL,
                size REAL NOT NULL,
                fee_paid REAL DEFAULT 0,
                rebate_earned REAL DEFAULT 0,
                net_pnl REAL,
                route_used TEXT,
                outcome TEXT,
                order_id TEXT,
                resolved BOOLEAN DEFAULT 0,
                resolution_timestamp DATETIME
            )
        """)

        # Hourly PnL tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hourly_pnl (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hour_start DATETIME NOT NULL UNIQUE,
                hour_end DATETIME NOT NULL,
                start_capital REAL NOT NULL,
                end_capital REAL NOT NULL,
                net_pnl REAL NOT NULL,
                trades_count INTEGER DEFAULT 0,
                target_met BOOLEAN DEFAULT 0,
                win_rate REAL,
                avg_pnl_per_trade REAL
            )
        """)

        # Errors and events
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                module TEXT NOT NULL,
                error_type TEXT NOT NULL,
                message TEXT NOT NULL,
                resolved BOOLEAN DEFAULT 0,
                resolution_timestamp DATETIME
            )
        """)

        # Positions tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                market_id TEXT NOT NULL,
                market_name TEXT,
                side TEXT NOT NULL,
                entry_price REAL NOT NULL,
                size REAL NOT NULL,
                entry_timestamp DATETIME NOT NULL,
                exit_price REAL,
                exit_timestamp DATETIME,
                pnl REAL,
                status TEXT DEFAULT 'OPEN'
            )
        """)

        # Performance metrics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                total_capital REAL NOT NULL,
                deployed_capital REAL NOT NULL,
                available_capital REAL NOT NULL,
                total_pnl REAL NOT NULL,
                win_rate REAL,
                sharpe_ratio REAL,
                max_drawdown REAL,
                total_trades INTEGER DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")

    def log_trade(self, trade_data: Dict[str, Any]) -> int:
        """Log a trade to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO trades (
                timestamp, market_id, market_name, strategy_type, side,
                price, size, fee_paid, rebate_earned, net_pnl,
                route_used, order_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            trade_data.get("market_id"),
            trade_data.get("market_name"),
            trade_data.get("strategy_type"),
            trade_data.get("side"),
            trade_data.get("price"),
            trade_data.get("size"),
            trade_data.get("fee_paid", 0),
            trade_data.get("rebate_earned", 0),
            trade_data.get("net_pnl"),
            trade_data.get("route_used"),
            trade_data.get("order_id"),
        ))

        trade_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(
            f"Trade logged: {trade_data['strategy_type']} | "
            f"{trade_data['side']} {trade_data['size']} @ ${trade_data['price']:.3f} | "
            f"PnL: ${trade_data.get('net_pnl', 0):.2f}"
        )

        return trade_id

    def log_position_open(self, position_data: Dict[str, Any]) -> int:
        """Log opening a position"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO positions (
                market_id, market_name, side, entry_price, size, entry_timestamp, status
            ) VALUES (?, ?, ?, ?, ?, ?, 'OPEN')
        """, (
            position_data["market_id"],
            position_data.get("market_name"),
            position_data["side"],
            position_data["entry_price"],
            position_data["size"],
            datetime.now().isoformat(),
        ))

        position_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return position_id

    def log_position_close(self, position_id: int, exit_price: float, pnl: float):
        """Log closing a position"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE positions
            SET exit_price = ?, exit_timestamp = ?, pnl = ?, status = 'CLOSED'
            WHERE id = ?
        """, (exit_price, datetime.now().isoformat(), pnl, position_id))

        conn.commit()
        conn.close()

    def log_error(self, module: str, error_type: str, message: str):
        """Log an error to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO errors (timestamp, module, error_type, message, resolved)
            VALUES (?, ?, ?, ?, 0)
        """, (datetime.now().isoformat(), module, error_type, message))

        conn.commit()
        conn.close()

        logger.error(f"[{module}] {error_type}: {message}")

    def update_hourly_pnl(self, start_capital: float, end_capital: float, trades_count: int):
        """Update hourly PnL tracking"""
        hour_start = datetime.now().replace(minute=0, second=0, microsecond=0)
        hour_end = hour_start + timedelta(hours=1)
        net_pnl = end_capital - start_capital
        target_met = net_pnl >= config.hourly_profit_target

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get win rate for this hour
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) as wins
            FROM trades
            WHERE timestamp >= ? AND timestamp < ?
        """, (hour_start.isoformat(), hour_end.isoformat()))

        result = cursor.fetchone()
        win_rate = (result[1] / result[0] * 100) if result[0] > 0 else 0
        avg_pnl = net_pnl / trades_count if trades_count > 0 else 0

        cursor.execute("""
            INSERT OR REPLACE INTO hourly_pnl (
                hour_start, hour_end, start_capital, end_capital,
                net_pnl, trades_count, target_met, win_rate, avg_pnl_per_trade
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            hour_start.isoformat(),
            hour_end.isoformat(),
            start_capital,
            end_capital,
            net_pnl,
            trades_count,
            target_met,
            win_rate,
            avg_pnl,
        ))

        conn.commit()
        conn.close()

    def get_hourly_stats(self) -> Dict[str, Any]:
        """Get statistics for the current hour"""
        hour_start = datetime.now().replace(minute=0, second=0, microsecond=0)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*), SUM(net_pnl), AVG(net_pnl)
            FROM trades
            WHERE timestamp >= ?
        """, (hour_start.isoformat(),))

        result = cursor.fetchone()
        conn.close()

        return {
            "trades_count": result[0] or 0,
            "total_pnl": result[1] or 0,
            "avg_pnl": result[2] or 0,
        }

    def get_daily_stats(self) -> Dict[str, Any]:
        """Get statistics for the current day"""
        day_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total_trades,
                SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                SUM(net_pnl) as total_pnl,
                AVG(net_pnl) as avg_pnl,
                MIN(net_pnl) as worst_trade,
                MAX(net_pnl) as best_trade
            FROM trades
            WHERE timestamp >= ?
        """, (day_start.isoformat(),))

        result = cursor.fetchone()
        conn.close()

        total_trades = result[0] or 0
        winning_trades = result[1] or 0

        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "win_rate": (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            "total_pnl": result[2] or 0,
            "avg_pnl": result[3] or 0,
            "worst_trade": result[4] or 0,
            "best_trade": result[5] or 0,
        }

    def get_open_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM positions WHERE status = 'OPEN'
        """)

        positions = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return positions

    def export_daily_report(self, date: Optional[datetime] = None) -> str:
        """Export daily trading report as CSV"""
        if date is None:
            date = datetime.now()

        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM trades
            WHERE timestamp >= ? AND timestamp < ?
            ORDER BY timestamp
        """, (day_start.isoformat(), day_end.isoformat()))

        trades = cursor.fetchall()
        conn.close()

        # Export to CSV
        csv_path = f"reports/trades_{date.strftime('%Y-%m-%d')}.csv"
        Path("reports").mkdir(exist_ok=True)

        with open(csv_path, "w") as f:
            f.write("Timestamp,Market,Strategy,Side,Price,Size,Fee,Rebate,PnL,Route\n")
            for trade in trades:
                f.write(f"{','.join(map(str, trade))}\n")

        logger.info(f"Daily report exported to {csv_path}")
        return csv_path


# Singleton instance
trading_logger = TradingLogger()
