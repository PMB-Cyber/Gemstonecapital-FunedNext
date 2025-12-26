import time
import threading
from queue import Queue
from config.allowed_symbols import ALLOWED_SYMBOLS

from monitoring.logger import logger
from monitoring.heartbeat import print_status
from monitoring.profit_lock import check_profit_lock
from monitoring.equity_kill_switch import is_locked

from trading_core.risk_manager import RiskManager
from trading_core.capital_scaler import CapitalScaler
from trading_core.execution_flags import ExecutionFlags, AccountPhase, ExecutionMode, MLMode
from trading_core.trade_gatekeeper import TradeGatekeeper
from trading_core.ml_router import MLRouter
from trading_core.session_controller import SessionController
from execution.order_router import OrderRouter
from execution.mt5_data_feed import MT5DataFeed
from execution.trailing_sl_manager import TrailingSLManager
from execution.partial_tp_manager import PartialTPManager
from trading_core.signal_engine import SignalEngine
from monitoring.startup_validator import StartupValidator

# =========================
# CONFIG
# =========================
TIMEFRAME_BARS = 300
LOOP_SLEEP_SECONDS = 60
SHADOW_MODE = True
PER_SYMBOL_THROTTLE = 0.3

ATR_PERIOD = 14
ATR_SL_MULTIPLIER = 1.2
ATR_TP_MULTIPLIERS = (1.0, 2.0)
TP_CLOSE_PERCENTS = (0.3, 0.3)


# =========================
# SYMBOL WORKER THREAD
# =========================
def symbol_worker(symbol, feed, signal_engine, ml_router, risk_manager, trade_gatekeeper, order_router,
                  partial_tp_manager, trailing_sl_manager, execution_flags):
    df = feed.get_candles(symbol, TIMEFRAME_BARS)
    if df is None or df.empty or len(df) < 50:
        logger.warning(f"{symbol}: insufficient candle data")
        return

    # Prepare features & ML inference
    features = signal_engine.prepare_features(df)
    ml_signal = ml_router.infer(features)
    if execution_flags.ml_mode == MLMode.TRAINING:
        ml_router.update_model(features, df)

    # Trade management
    partial_tp_manager.manage(symbol, df)
    trailing_sl_manager.manage(symbol, df)

    # Final signal
    signal = ml_signal if ml_signal else signal_engine.generate_signal(df, symbol)
    if not signal:
        return

    side, score = signal
    logger.info(f"SIGNAL | {symbol} | {side.upper()} | score={score:.2f}")

    # ATR-based stop loss
    atr = trailing_sl_manager._calculate_atr(df)
    stop_loss_pips = max(1, round(atr * ATR_SL_MULTIPLIER))

    # Position sizing
    volume = risk_manager.position_size(symbol, stop_loss_pips)
    risk_amount = stop_loss_pips * 10 * volume
    if volume <= 0 or not risk_manager.can_open_trade(risk_amount):
        return

    # Trade gatekeeper
    allowed, reason = trade_gatekeeper.authorize_trade(symbol, risk_amount)
    if not allowed:
        logger.warning(f"{symbol}: trade blocked — {reason}")
        return

    # Place order
    order = order_router.route_order(
        symbol=symbol,
        order_type=side,
        volume=volume,
        stop_loss=stop_loss_pips,
        take_profit=None,
        comment="FundedNext Orchestrated ATR"
    )

    if order["status"] in ("filled", "simulated"):
        logger.success(f"ORDER EXECUTED | {symbol} | {side.upper()} | vol={volume}")
    else:
        logger.error(f"{symbol}: order failed | reason={order.get('reason')}")


# =========================
# ORCHESTRATOR LOOP
# =========================
def start_orchestrated_system():
    logger.info("🚀 Starting Full Orchestrated FundedNext System (ATR-Adaptive TP/SL)")

    # -------------------------
    # STARTUP VALIDATION
    # -------------------------
    StartupValidator().validate_or_die()

    # -------------------------
    # CORE COMPONENTS
    # -------------------------
    execution_flags = ExecutionFlags(
        account_phase=AccountPhase.CHALLENGE,
        execution_mode=ExecutionMode.SHADOW if SHADOW_MODE else ExecutionMode.LIVE,
        ml_mode=MLMode.TRAINING
    )

    risk_manager = RiskManager()
    capital_scaler = CapitalScaler(start_balance=risk_manager.start_balance)
    trade_gatekeeper = TradeGatekeeper(execution_flags, risk_manager)
    ml_router = MLRouter(execution_flags)
    session_controller = SessionController(execution_flags, risk_manager)

    order_router = OrderRouter(execution_flags)
    feed = MT5DataFeed()
    signal_engine = SignalEngine(confidence_threshold=0.7)

    partial_tp_manager = PartialTPManager(
        tp_multipliers=ATR_TP_MULTIPLIERS,
        close_percents=TP_CLOSE_PERCENTS,
        atr_period=ATR_PERIOD,
        atr_multiplier=ATR_SL_MULTIPLIER
    )

    trailing_sl_manager = TrailingSLManager(
        atr_period=ATR_PERIOD,
        atr_multiplier=ATR_SL_MULTIPLIER
    )

    logger.success("System booted successfully (Full Orchestration + ATR-Adaptive TP/SL)")

    try:
        while True:
            # -------------------------
            # DAILY MAINTENANCE
            # -------------------------
            session_controller.daily_maintenance()
            print_status()

            # -------------------------
            # GLOBAL HARD STOPS
            # -------------------------
            if is_locked() or not check_profit_lock() or risk_manager.hard_stop_triggered():
                logger.warning("System paused due to hard stop / profit lock / equity lock")
                time.sleep(300)
                continue

            # -------------------------
            # SYMBOL THREADS
            # -------------------------
            threads = []
            for symbol in ALLOWED_SYMBOLS:
                t = threading.Thread(target=symbol_worker, args=(
                    symbol, feed, signal_engine, ml_router, risk_manager,
                    trade_gatekeeper, order_router, partial_tp_manager,
                    trailing_sl_manager, execution_flags
                ))
                t.start()
                threads.append(t)
                time.sleep(PER_SYMBOL_THROTTLE)

            for t in threads:
                t.join()

            # -------------------------
            # LOOP SLEEP
            # -------------------------
            time.sleep(LOOP_SLEEP_SECONDS)

    except KeyboardInterrupt:
        logger.warning("🛑 Manual shutdown detected")

    except Exception as e:
        logger.exception(f"💥 Fatal runtime error: {e}")

    finally:
        feed.shutdown()
        logger.info("Orchestrated system shutdown complete")


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    logger.info("🚀 FundedNext Orchestrated System STARTED")
    start_orchestrated_system()
