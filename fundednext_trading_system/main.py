import time
import threading
import pandas as pd
import pickle
import os
import sys

# Conditional MT5 import:
# If in production, remove the current directory from the path to ensure the system
# uses the installed MetaTrader5 package instead of the local mock version.
from config.settings import ENVIRONMENT
if ENVIRONMENT == "production":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir in sys.path:
        sys.path.remove(current_dir)

import MetaTrader5 as mt5

from config.allowed_symbols import ALLOWED_SYMBOLS
from execution.symbol_stats_manager import SymbolStatsManager
from monitoring.logger import logger
from monitoring.profit_lock import check_profit_lock
from monitoring.equity_kill_switch import is_locked
from monitoring.startup_validator import StartupValidator
from monitoring.heartbeat import print_status as heartbeat_console
from monitoring.discord_logger import broadcast, send_discord_update

from trading_core.risk_manager import RiskManager
from trading_core.execution_flags import ExecutionFlags, AccountPhase, ExecutionMode, MLMode
from trading_core.trade_gatekeeper import TradeGatekeeper
from trading_core.ml_router import MLRouter
from trading_core.session_controller import SessionController
from trading_core.signal_engine import SignalEngine

from execution.mt5_data_feed import MT5DataFeed
from execution.order_router import OrderRouter
from execution.trailing_sl_manager import TrailingSLManager
from execution.partial_tp_manager import PartialTPManager

from config.settings import (
    TIMEFRAME_BARS,
    LOOP_SLEEP_SECONDS,
    PER_SYMBOL_THROTTLE,
    ATR_PERIOD,
    ATR_SL_MULTIPLIER,
    ATR_TP_MULTIPLIERS,
    TP_CLOSE_PERCENTS,
    DRY_RUN,
    REPLAY_MODE,
    ML_MODEL_PATH,
    STATS_PATH,
    ACCOUNT_PHASE,
    EXECUTION_MODE,
    ML_MODE,
    ENVIRONMENT
)

# =========================================================
# MARKET READY / SPREAD CHECK
# =========================================================
def wait_for_market_ready(max_wait_seconds: int = 600):
    logger.info("⏳ Waiting for market to be ready (spread stabilization)")
    start = time.time()

    while True:
        all_ok = True
        for symbol in ALLOWED_SYMBOLS:
            tick = mt5.symbol_info_tick(symbol)
            info = mt5.symbol_info(symbol)

            if tick is None or info is None:
                logger.warning(f"{symbol}: tick/info unavailable")
                all_ok = False
                continue

            spread_pts = abs(tick.ask - tick.bid) / info.point
            if spread_pts > max(30, spread_pts * 1.5):
                logger.warning(f"{symbol}: spread too high ({spread_pts:.1f} pts)")
                all_ok = False

        if all_ok:
            logger.success("✅ Market ready — spreads acceptable")
            return

        if time.time() - start > max_wait_seconds:
            logger.warning("⏰ Max wait reached — proceeding anyway")
            return

        time.sleep(5)

# =========================================================
# REGIME DETECTION
# =========================================================
def detect_market_regime(df: pd.DataFrame, ma_period: int = 50) -> str:
    if len(df) < ma_period + 2:
        return "range"

    ma = df["close"].rolling(ma_period).mean()
    slope = ma.iloc[-1] - ma.iloc[-2]
    threshold = df["close"].std() * 0.1

    return "trend" if abs(slope) > threshold else "range"

# =========================================================
# SYMBOL WORKER
# =========================================================
def symbol_worker(
    symbol: str,
    feed: MT5DataFeed,
    signal_engine: SignalEngine,
    ml_router: MLRouter,
    risk_manager: RiskManager,
    trade_gatekeeper: TradeGatekeeper,
    order_router: OrderRouter,
    partial_tp_manager: PartialTPManager,
    trailing_sl_manager: TrailingSLManager,
    execution_flags: ExecutionFlags,
    stats_manager: SymbolStatsManager,
):
    df = feed.get_candles(symbol, TIMEFRAME_BARS)
    if df is None or df.empty or len(df) < 60:
        logger.debug(f"{symbol}: insufficient candle data")
        return

    # -----------------------------------------------------
    # Manage open positions
    # -----------------------------------------------------
    partial_tp_manager.manage(symbol, df)
    trailing_sl_manager.manage(symbol, df)

    # -----------------------------------------------------
    # Regime detection
    # -----------------------------------------------------
    regime = detect_market_regime(df)
    stats_manager.stats[symbol]["regime"] = regime

    # -----------------------------------------------------
    # Feature prep + ML inference
    # -----------------------------------------------------
    features = signal_engine.prepare_features(df, regime=regime)
    ml_signal = ml_router.infer(features)

    # Confidence gating
    if ml_signal and ml_signal[1] < 0.7:
        ml_signal = None  # Use rule-based signal if confidence is low

    if execution_flags.ml_mode == MLMode.TRAINING:
        ml_router.update_model(features, df)

    # -----------------------------------------------------
    # Rule-based fallback ALWAYS allowed
    # -----------------------------------------------------
    signal = ml_signal or signal_engine.generate_signal(df, symbol, regime=regime)
    if not signal:
        return

    side, score = signal
    logger.info(f"SIGNAL | {symbol} | {side.upper()} | score={score:.2f} | regime={regime}")

    # -----------------------------------------------------
    # Risk & position sizing
    # -----------------------------------------------------
    atr = trailing_sl_manager._calculate_atr(df)
    stop_loss_pips = max(1, round(atr * ATR_SL_MULTIPLIER))

    volume = risk_manager.position_size(symbol, stop_loss_pips)
    risk_amount = stop_loss_pips * 10 * volume

    if volume <= 0 or not risk_manager.can_open_trade(risk_amount):
        return

    allowed, reason = trade_gatekeeper.authorize_trade(symbol, risk_amount)
    if not allowed:
        logger.warning(f"{symbol}: trade blocked — {reason}")
        return

    # -----------------------------------------------------
    # Dry-run / Replay
    # -----------------------------------------------------
    if DRY_RUN or REPLAY_MODE:
        logger.info(f"{symbol}: DRY-RUN | {side.upper()} | vol={volume}")
        stats_manager.stats[symbol]["trades"] += 1
        return

    # -----------------------------------------------------
    # Execute order
    # -----------------------------------------------------
    order = order_router.route_order(
        symbol=symbol,
        order_type=side,
        volume=volume,
        stop_loss=stop_loss_pips,
        take_profit=None,
        comment="FundedNext Live Orchestrator",
    )

    if order.get("status") in ("filled", "simulated"):
        logger.success(f"ORDER EXECUTED | {symbol} | {side.upper()} | vol={volume}")
        stats_manager.stats[symbol]["trades"] += 1
    else:
        logger.error(f"{symbol}: order failed | {order}")

# =========================================================
# HEARTBEAT WORKER
# =========================================================
def heartbeat_worker(
    risk_manager,
    execution_flags,
    feed,
    partial_tp_manager,
    trailing_sl_manager,
    ml_router,
    stats_manager,
):
    heartbeat_console(
        risk_manager=risk_manager,
        execution_flags=execution_flags,
        feed=feed,
        partial_tp_manager=partial_tp_manager,
        trailing_sl_manager=trailing_sl_manager,
        ml_router=ml_router,
        symbol_stats=stats_manager.stats,
        refresh_seconds=15,
    )

# =========================================================
# MT5 READINESS CHECK
# =========================================================
def mt5_readiness_check():
    if not mt5.initialize():
        raise SystemExit("❌ MT5 initialization failed")

    for symbol in ALLOWED_SYMBOLS:
        if mt5.symbol_info(symbol) is None:
            raise SystemExit(f"{symbol} not available")

    mt5.shutdown()
    logger.success("🎯 MT5 readiness check passed")

# =========================================================
# PERSIST ML MODEL AND STATS
# =========================================================
def save_ml_model_and_stats(model, stats):
    with open(ML_MODEL_PATH, "wb") as model_file:
        pickle.dump(model, model_file)
    with open(STATS_PATH, "wb") as stats_file:
        pickle.dump(stats, stats_file)
    logger.success("ML Model and Stats saved successfully.")

def load_ml_model_and_stats():
    if os.path.exists(ML_MODEL_PATH) and os.path.exists(STATS_PATH):
        with open(ML_MODEL_PATH, "rb") as model_file:
            model = pickle.load(model_file)
        with open(STATS_PATH, "rb") as stats_file:
            stats = pickle.load(stats_file)
        logger.success("ML Model and Stats loaded successfully.")
        return model, stats
    return None, None

# =========================================================
# MAIN ORCHESTRATOR
# =========================================================
def start_master_orchestrator():
    logger.info("🚀 Starting FundedNext Live Orchestrator")

    mt5_readiness_check()
    StartupValidator().validate_or_die()

    logger.info(f"Environment set to: {ENVIRONMENT.upper()}")

    execution_flags = ExecutionFlags(
        account_phase=AccountPhase[ACCOUNT_PHASE],
        execution_mode=ExecutionMode[EXECUTION_MODE],
        ml_mode=MLMode[ML_MODE],
    )

    risk_manager = RiskManager()
    trade_gatekeeper = TradeGatekeeper(execution_flags, risk_manager)
    ml_router = MLRouter(execution_flags)
    session_controller = SessionController(execution_flags, risk_manager)

    feed = MT5DataFeed()
    signal_engine = SignalEngine(confidence_threshold=0.7)
    order_router = OrderRouter(execution_flags)

    partial_tp_manager = PartialTPManager(
        tp_multipliers=ATR_TP_MULTIPLIERS,
        close_percents=TP_CLOSE_PERCENTS,
        atr_period=ATR_PERIOD,
        atr_multiplier=ATR_SL_MULTIPLIER,
    )

    trailing_sl_manager = TrailingSLManager(
        atr_period=ATR_PERIOD,
        atr_multiplier=ATR_SL_MULTIPLIER,
    )

    stats_manager = SymbolStatsManager()
    for sym in ALLOWED_SYMBOLS:
        stats_manager.init_symbol(sym)

    # Load saved model and stats
    ml_model, stats = load_ml_model_and_stats()
    if ml_model:
        ml_router.model = ml_model
    else:
        logger.error("No pre-trained model found. Shutting down.")
        return

    if not DRY_RUN:
        wait_for_market_ready()

    logger.success("✅ System initialized successfully")

    threading.Thread(
        target=heartbeat_worker,
        args=(
            risk_manager,
            execution_flags,
            feed,
            partial_tp_manager,
            trailing_sl_manager,
            ml_router,
            stats_manager,
        ),
        daemon=True,
    ).start()

    try:
        while True:
            session_controller.daily_maintenance()

            if is_locked() or not check_profit_lock() or risk_manager.hard_stop_triggered():
                logger.warning("⛔ Trading paused — risk controls active")
                time.sleep(300)
                continue

            threads = []
            for symbol in ALLOWED_SYMBOLS:
                t = threading.Thread(
                    target=symbol_worker,
                    args=(
                        symbol,
                        feed,
                        signal_engine,
                        ml_router,
                        risk_manager,
                        trade_gatekeeper,
                        order_router,
                        partial_tp_manager,
                        trailing_sl_manager,
                        execution_flags,
                        stats_manager,
                    ),
                )
                t.start()
                threads.append(t)
                time.sleep(PER_SYMBOL_THROTTLE)

            for t in threads:
                t.join()

            time.sleep(LOOP_SLEEP_SECONDS)

    except KeyboardInterrupt:
        logger.warning("🛑 Manual shutdown")

    finally:
        # Save model and stats at the end of the session, if in a training mode
        if execution_flags.ml_mode == MLMode.TRAINING:
            save_ml_model_and_stats(ml_router.model, stats_manager.stats)
        feed.shutdown()
        logger.info("Orchestrator shutdown complete")

# =========================================================
# ENTRY POINT
# =========================================================
if __name__ == "__main__":
    start_master_orchestrator()
