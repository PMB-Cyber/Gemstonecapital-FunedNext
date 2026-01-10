from __future__ import annotations
import os
from datetime import date
from fundednext_trading_system.config.settings import ENVIRONMENT

if ENVIRONMENT == "development":
    from fundednext_trading_system.MetaTrader5 import MetaTrader5 as mt5
else:
    import MetaTrader5 as mt5

from fundednext_trading_system.monitoring.logger import logger
from fundednext_trading_system.monitoring.discord_logger import broadcast


# =========================
# CONFIG — HARD LIMITS
# =========================
STARTING_BALANCE = 5000.0
MAX_DAILY_DD = 0.02     # 2%
MAX_TOTAL_DD = 0.04     # 4%

# =========================
# INTERNAL STATE
# =========================
DAILY_START_EQUITY = None
LAST_RESET_DATE = None

LOCKED = False
LOCK_REASON = None

LIQUIDATION_TRIGGERED = False


# =========================
# MT5 HELPERS
# =========================
def _get_account_equity():
    info = mt5.account_info()
    if info is None:
        logger.error("MT5 account info unavailable")
        return None
    return float(info.equity)


# =========================
# DAILY RESET
# =========================
def reset_daily_equity():
    global DAILY_START_EQUITY, LAST_RESET_DATE

    equity = _get_account_equity()
    if equity is None:
        return

    DAILY_START_EQUITY = equity
    LAST_RESET_DATE = date.today()

    logger.info(f"Daily equity baseline reset: ${equity:.2f}")
    broadcast(f"🔄 Daily equity reset → ${equity:.2f}")


# =========================
# EQUITY CHECK
# =========================
def check_equity_limits():
    global LOCKED, LOCK_REASON

    if LOCKED:
        return False

    equity = _get_account_equity()
    if equity is None:
        return False

    today = date.today()

    # Daily reset
    if LAST_RESET_DATE != today or DAILY_START_EQUITY is None:
        reset_daily_equity()

    total_dd = (STARTING_BALANCE - equity) / STARTING_BALANCE
    daily_dd = (DAILY_START_EQUITY - equity) / DAILY_START_EQUITY

    if total_dd >= MAX_TOTAL_DD:
        LOCK_REASON = "MAX TOTAL DRAWDOWN HIT"
    elif daily_dd >= MAX_DAILY_DD:
        LOCK_REASON = "MAX DAILY DRAWDOWN HIT"
    else:
        return True

    # 🔥 LOCK SYSTEM
    LOCKED = True

    msg = (
        f"🛑 EQUITY KILL SWITCH ACTIVATED\n"
        f"Reason: {LOCK_REASON}\n"
        f"Equity: ${equity:.2f}"
    )

    logger.critical(msg)
    broadcast(msg)

    trigger_emergency_liquidation()

    return False


# =========================
# EMERGENCY LIQUIDATION
# =========================
def trigger_emergency_liquidation():
    global LIQUIDATION_TRIGGERED

    if LIQUIDATION_TRIGGERED:
        logger.warning("Emergency liquidation already executed — skipping")
        return

    LIQUIDATION_TRIGGERED = True

    logger.critical("🔥 EMERGENCY LIQUIDATION INITIATED")
    broadcast("🔥 EMERGENCY LIQUIDATION INITIATED")

    positions = mt5.positions_get()
    if not positions:
        logger.warning("No open positions to liquidate")
        return

    for pos in positions:
        tick = mt5.symbol_info_tick(pos.symbol)
        if tick is None:
            logger.error(f"Tick data unavailable for {pos.symbol}")
            continue

        close_type = (
            mt5.ORDER_TYPE_SELL
            if pos.type == mt5.ORDER_TYPE_BUY
            else mt5.ORDER_TYPE_BUY
        )

        price = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "position": pos.ticket,
            "volume": pos.volume,
            "type": close_type,
            "price": price,
            "deviation": 20,
            "magic": 777001,
            "comment": "EMERGENCY_LIQUIDATION",
        }

        result = mt5.order_send(request)

        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.success(
                f"Liquidated {pos.symbol} | ticket={pos.ticket}"
            )
        else:
            logger.error(
                f"FAILED liquidation {pos.symbol} | ticket={pos.ticket}"
            )


# =========================
# STATUS HELPERS
# =========================
def is_locked():
    return LOCKED


def get_lock_reason():
    return LOCK_REASON
