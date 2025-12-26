import time
import os

from config.allowed_symbols import ALLOWED_SYMBOLS
from config.execution_flags import is_execution_allowed

from execution.session_filter import SessionFilter
from execution.trailing_sl_manager import TrailingSLManager
from execution.partial_tp_manager import PartialTPManager

from monitoring.profit_lock import check_profit_lock
from monitoring.equity_kill_switch import is_locked, get_lock_reason
from monitoring.logger import logger
from monitoring.heartbeat import print_status

from trading_core.signal_engine import SignalEngine
from trading_core.risk_manager import RiskManager

from execution.mt5_executor import MT5Executor
from execution.mt5_data_feed import MT5DataFeed


# =========================
# CONFIG
# =========================
TIMEFRAME_BARS = 300
LOOP_SLEEP_SECONDS = 60

STOP_LOSS_PIPS = 10
TAKE_PROFIT_PIPS = 20


# =========================
# MAIN LOOP
# =========================
def start_trading_system():
    logger.info("🚀 Initializing FundedNext Trading System")

    feed = MT5DataFeed()
    executor = MT5Executor()
    signal_engine = SignalEngine(confidence_threshold=0.7)
    risk_manager = RiskManager()

    trailing_sl_manager = TrailingSLManager()
    partial_tp_manager = PartialTPManager()

    session_filter = SessionFilter(
        allow_london=True,
        allow_ny=True,
    )

    logger.success("System booted successfully")

    try:
        while True:
            # -------------------------
            # HEARTBEAT
            # -------------------------
            print_status()

            # -------------------------
            # GLOBAL HARD STOPS
            # -------------------------
            if is_locked():
                logger.critical(
                    f"⛔ EQUITY LOCK ACTIVE — {get_lock_reason()}"
                )
                time.sleep(300)
                continue

            if risk_manager.hard_stop_triggered():
                logger.critical(
                    "🚨 HARD RISK STOP — SYSTEM PAUSED"
                )
                time.sleep(600)
                continue

            if not check_profit_lock():
                logger.critical(
                    "🔒 PROFIT LOCK ACTIVE — SYSTEM PAUSED"
                )
                time.sleep(300)
                continue

            if not session_filter.is_trading_allowed():
                logger.info(
                    "⏰ Outside allowed trading session"
                )
                time.sleep(300)
                continue

            # -------------------------
            # MULTI-SYMBOL LOOP
            # -------------------------
            for symbol in ALLOWED_SYMBOLS:
                df = feed.get_candles(
                    symbol=symbol,
                    bars=TIMEFRAME_BARS,
                )

                if df is None or df.empty or len(df) < 50:
                    logger.warning(
                        f"{symbol}: insufficient candle data"
                    )
                    continue

                # -------------------------
                # POSITION MANAGEMENT
                # -------------------------
                partial_tp_manager.manage(symbol)
                trailing_sl_manager.manage(symbol, df)

                # -------------------------
                # SIGNAL GENERATION
                # -------------------------
                signal = signal_engine.generate_signal(df, symbol)
                if not signal:
                    continue

                side, score = signal

                logger.info(
                    f"SIGNAL | {symbol} | "
                    f"{side.upper()} | score={score:.2f}"
                )

                # -------------------------
                # EXECUTION ARMING GATE
                # -------------------------
                if not is_execution_allowed(
                    challenge_passed=risk_manager.challenge_passed
                ):
                    logger.warning(
                        f"{symbol}: execution DISARMED — "
                        f"mode={risk_manager.mode}"
                    )
                    continue

                # -------------------------
                # POSITION SIZE
                # -------------------------
                volume = risk_manager.position_size(
                    symbol=symbol,
                    stop_loss_pips=STOP_LOSS_PIPS,
                )

                if volume <= 0:
                    logger.warning(
                        f"{symbol}: zero volume — trade skipped"
                    )
                    continue

                risk_amount = STOP_LOSS_PIPS * 10 * volume

                if not risk_manager.can_open_trade(risk_amount):
                    logger.warning(
                        f"{symbol}: risk rules block trade"
                    )
                    continue

                # -------------------------
                # EXECUTION
                # -------------------------
                order = executor.place_order(
                    symbol=symbol,
                    signal=side,
                    stop_loss_pips=STOP_LOSS_PIPS,
                    take_profit_pips=TAKE_PROFIT_PIPS,
                    volume=volume,
                )

                if order:
                    logger.success(
                        f"ORDER EXECUTED | {symbol} | "
                        f"{side.upper()} | vol={volume}"
                    )
                else:
                    logger.error(
                        f"{symbol}: order execution failed"
                    )

            time.sleep(LOOP_SLEEP_SECONDS)

    except KeyboardInterrupt:
        logger.warning("🛑 Manual shutdown detected")

    except Exception as e:
        logger.exception(
            f"💥 Fatal runtime error: {e}"
        )

    finally:
        feed.shutdown()
        executor.shutdown()
        logger.info(
            "Trading system shutdown complete"
        )


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    logger.info("🚀 FundedNext Trading System STARTED")
    start_trading_system()
