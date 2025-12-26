import MetaTrader5 as mt5
from monitoring.logger import logger
from monitoring.discord_logger import broadcast
from monitoring.equity_kill_switch import trigger_emergency_liquidation


# =========================
# CONFIG
# =========================
STARTING_BALANCE = 5000.0
ACTIVATION_PROFIT_PCT = 0.02    # +2%
LOCK_IN_RATIO = 0.50            # Lock 50% of profits


# =========================
# STATE
# =========================
PROFIT_LOCK_ACTIVE = False
LOCKED_EQUITY_FLOOR = None


# =========================
# HELPERS
# =========================
def _get_equity():
    info = mt5.account_info()
    if info is None:
        logger.error("MT5 account info unavailable")
        return None
    return float(info.equity)


# =========================
# PROFIT LOCK CHECK
# =========================
def check_profit_lock():
    global PROFIT_LOCK_ACTIVE, LOCKED_EQUITY_FLOOR

    equity = _get_equity()
    if equity is None:
        return True

    profit = equity - STARTING_BALANCE
    profit_pct = profit / STARTING_BALANCE

    # -------------------------
    # ACTIVATE PROFIT LOCK
    # -------------------------
    if not PROFIT_LOCK_ACTIVE and profit_pct >= ACTIVATION_PROFIT_PCT:
        locked_amount = profit * LOCK_IN_RATIO
        LOCKED_EQUITY_FLOOR = STARTING_BALANCE + locked_amount
        PROFIT_LOCK_ACTIVE = True

        msg = (
            f"🔒 PROFIT LOCK ACTIVATED\n"
            f"Equity: ${equity:.2f}\n"
            f"Locked Floor: ${LOCKED_EQUITY_FLOOR:.2f}"
        )

        logger.success(msg)
        broadcast(msg)
        return True

    # -------------------------
    # TRAILING FLOOR UP
    # -------------------------
    if PROFIT_LOCK_ACTIVE:
        new_floor = STARTING_BALANCE + (profit * LOCK_IN_RATIO)
        if new_floor > LOCKED_EQUITY_FLOOR:
            LOCKED_EQUITY_FLOOR = new_floor
            logger.info(
                f"🔼 Profit lock trailed → ${LOCKED_EQUITY_FLOOR:.2f}"
            )

        # -------------------------
        # BREACH
        # -------------------------
        if equity < LOCKED_EQUITY_FLOOR:
            msg = (
                f"🚨 PROFIT LOCK BREACHED\n"
                f"Equity: ${equity:.2f}\n"
                f"Floor: ${LOCKED_EQUITY_FLOOR:.2f}"
            )

            logger.critical(msg)
            broadcast(msg)

            trigger_emergency_liquidation()
            return False

    return True
