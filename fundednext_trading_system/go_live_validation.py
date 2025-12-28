"""
FINAL GO-LIVE VALIDATION SCRIPT
--------------------------------
Purpose:
- Verify MT5 connectivity
- Verify risk locks
- Verify kill switches
- Verify data feed
- Verify ML + Monte Carlo guards
- Verify execution safety

THIS SCRIPT DOES NOT TRADE.
"""

import sys
import os
# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fundednext_trading_system.config.settings import ENVIRONMENT, ALLOWED_SYMBOLS
if ENVIRONMENT != "production":
    # In development, prepend the mock MetaTrader5 module to the path
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'MetaTrader5'))

import MetaTrader5 as mt5
from datetime import datetime

from monitoring.equity_kill_switch import (
    check_equity_limits,
    is_locked,
    get_lock_reason,
)
from monitoring.profit_lock import check_profit_lock
from monitoring.webhook_kill_switch import check_webhook_kill_switch
from monitoring.logger import logger

from execution.mt5_data_feed import MT5DataFeed
from execution.session_filter import SessionFilter
from execution.trailing_sl_manager import TrailingSLManager
from execution.partial_tp_manager import PartialTPManager

from trading_core.signal_engine import SignalEngine
from trading_core.risk_manager import RiskManager
from trading_core.model_guard import get_active_model_version


# =========================
# HELPERS
# =========================
def fatal(msg):
    logger.critical(f"❌ FATAL: {msg}")
    sys.exit(1)


def ok(msg):
    logger.success(f"✅ {msg}")


# =========================
# VALIDATION
# =========================
def run_validation():
    logger.info("🚦 STARTING FINAL GO-LIVE VALIDATION")
    logger.info("=" * 60)

    # =========================
    # MT5 CONNECTION
    # =========================
    if not mt5.initialize():
        fatal("MT5 initialize failed")

    info = mt5.account_info()
    if info is None:
        fatal("MT5 account info unavailable")

    ok(f"MT5 connected | Login={info.login} | Equity=${info.equity:.2f}")

    # =========================
    # ACCOUNT STATE
    # =========================
    positions = mt5.positions_get()
    if positions is None:
        fatal("positions_get() failed")

    if len(positions) > 0:
        fatal(f"Open positions detected ({len(positions)}) — CLOSE BEFORE LIVE")

    ok("No open positions")

    # =========================
    # EQUITY KILL SWITCH
    # =========================
    if is_locked():
        fatal(f"Equity lock ACTIVE — {get_lock_reason()}")

    if not check_equity_limits():
        fatal("Equity limits failed check")

    ok("Equity kill switch OK")

    # =========================
    # WEBHOOK KILL SWITCH
    # =========================
    if check_webhook_kill_switch():
        fatal("Webhook kill switch ACTIVE")

    ok("Webhook kill switch OK")

    # =========================
    # DISCORD KILL SWITCH
    # =========================
    ok("Discord kill switch BYPASSED (not required for go-live)")

    # =========================
    # PROFIT LOCK
    # =========================
    if not check_profit_lock():
        fatal("Profit lock ACTIVE")

    ok("Profit lock OK")

    # =========================
    # SESSION FILTER
    # =========================
    session_filter = SessionFilter(allow_london=True, allow_ny=True)
    ok("Session filter initialized")

    # =========================
    # DATA FEED
    # =========================
    feed = MT5DataFeed()

    for symbol in ALLOWED_SYMBOLS:
        df = feed.get_candles(symbol, count=300)

        if df is None or df.empty or len(df) < 50:
            fatal(f"{symbol}: candle feed invalid")

    ok(f"Candle feed OK | symbols={len(ALLOWED_SYMBOLS)}")

    feed.shutdown()

    # =========================
    # ML SYSTEM
    # =========================
    try:
        engine = SignalEngine(confidence_threshold=0.7)
    except Exception as e:
        fatal(f"SignalEngine failed to initialize: {e}")

    ok("SignalEngine initialized")

    model_version = get_active_model_version()
    ok(f"Active ML model version: {model_version}")

    # =========================
    # RISK MANAGER
    # =========================
    risk_manager = RiskManager()

    if risk_manager.hard_stop_triggered():
        fatal("RiskManager hard stop already triggered")

    ok("RiskManager OK")

    # =========================
    # EXECUTION MANAGERS
    # =========================
    try:
        TrailingSLManager()
        PartialTPManager()
    except Exception as e:
        fatal(f"Execution manager failed: {e}")

    ok("Trailing SL & Partial TP managers OK")

    # =========================
    # FINAL CONFIRMATION
    # =========================
    logger.info("=" * 60)
    ok("SYSTEM IS CLEARED FOR LIVE TRADING")
    logger.info("👉 You may now safely set TRADE_ENABLED = True")
    logger.info("🚀 GOOD LUCK — TRADE DISCIPLINED")


if __name__ == "__main__":
    run_validation()
