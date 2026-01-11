import time
import threading
import pandas as pd
import pickle
import os
import sys
import subprocess

# Conditional MT5 import:
# To ensure the correct MetaTrader5 package is used, the system path is temporarily
# modified in a production environment. This prevents the local mock version from
# being loaded and restores the path immediately after the import.
from fundednext_trading_system.config.settings import ENVIRONMENT

current_dir = os.path.dirname(os.path.abspath(__file__))
should_modify_path = (ENVIRONMENT == "production" and current_dir in sys.path)

if should_modify_path:
    sys.path.remove(current_dir)

try:
    import MetaTrader5 as mt5
finally:
    if should_modify_path:
        sys.path.insert(0, current_dir)

from fundednext_trading_system.execution.symbol_stats_manager import SymbolStatsManager
from fundednext_trading_system.monitoring.logger import logger
from fundednext_trading_system.monitoring.profit_lock import check_profit_lock
from fundednext_trading_system.monitoring.equity_kill_switch import is_locked
from fundednext_trading_system.monitoring.startup_validator import StartupValidator
from fundednext_trading_system.monitoring.heartbeat import print_status as heartbeat_console
from fundednext_trading_system.monitoring.discord_logger import broadcast, send_discord_update

from fundednext_trading_system.trading_core.risk_manager import RiskManager
from fundednext_trading_system.trading_core.execution_flags import ExecutionFlags, AccountPhase, ExecutionMode, MLMode
from fundednext_trading_system.trading_core.trade_gatekeeper import TradeGatekeeper
from fundednext_trading_system.trading_core.ml_router import MLRouter
from fundednext_trading_system.trading_core.session_controller import SessionController
from fundednext_trading_system.trading_core.signal_engine import SignalEngine
from fundednext_trading_system.trading_core.session_filter import SessionFilter
from fundednext_trading_system.trading_core.trade_selector import TradeSelector
from fundednext_trading_system.trading_core.correlation_manager import CorrelationManager

from fundednext_trading_system.execution.mt5_data_feed import MT5DataFeed
from fundednext_trading_system.execution.order_router import OrderRouter
from fundednext_trading_system.execution.trailing_sl_manager import TrailingSLManager
from fundednext_trading_system.execution.partial_tp_manager import PartialTPManager

from fundednext_trading_system.ml.retraining.retrain_model import retrain_model_for_symbol
from fundednext_trading_system.ml.model_loader import load_model_for_symbol

from fundednext_trading_system.config.settings import (
    TIMEFRAME_BARS,
    LOOP_SLEEP_SECONDS,
    PER_SYMBOL_THROTTLE,
    ATR_PERIOD,
    ATR_SL_MULTIPLIER,
    ATR_TP_MULTIPLIERS,
    TP_CLOSE_PERCENTS,
    DRY_RUN,
    REPLAY_MODE,
    STATS_PATH,
    ACCOUNT_PHASE,
    EXECUTION_MODE,
    ML_MODE,
    ENVIRONMENT,
    ALLOWED_SYMBOLS,
    RETRAIN_AFTER_N_TRADES,
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
# SIGNAL GENERATION WORKER
# =========================================================
def signal_generation_worker(
    symbol: str,
    feed: MT5DataFeed,
    signal_engine: SignalEngine,
    ml_router: MLRouter,
    stats_manager: SymbolStatsManager,
    execution_flags: ExecutionFlags,
    potential_trades: list
):
    df = feed.get_candles(symbol, mt5.TIMEFRAME_M1, TIMEFRAME_BARS)
    if df is None or df.empty or len(df) < 60:
        logger.debug(f"{symbol}: insufficient candle data")
        return

    # Load model for the symbol
    ml_router.model = load_model_for_symbol(symbol)
    if not ml_router.model:
        return # Skip if model not found

    # Regime detection
    regime = detect_market_regime(df)
    stats_manager.stats[symbol]["regime"] = regime

    # Feature prep + ML inference
    features = signal_engine.prepare_features(df, regime=regime)
    features, df = features.align(df, join='inner', axis=0)
    ml_signal = ml_router.infer(features)

    # Confidence gating
    if ml_signal and ml_signal[1] < 0.7:
        ml_signal = None

    if execution_flags.ml_mode == MLMode.TRAINING:
        ml_router.update_model(features, df)

    # Rule-based fallback
    signal = ml_signal or signal_engine.generate_signal(df, symbol, regime=regime)
    if signal:
        side, score = signal
        potential_trades.append({"symbol": symbol, "side": side, "score": score, "df": df})

# =========================================================
# TRADE EXECUTION WORKER
# =========================================================
def trade_execution_worker(
    trade: dict,
    risk_manager: RiskManager,
    trade_gatekeeper: TradeGatekeeper,
    order_router: OrderRouter,
    trailing_sl_manager: TrailingSLManager,
    execution_flags: ExecutionFlags,
    stats_manager: SymbolStatsManager,
):
    symbol = trade['symbol']
    side = trade['side']
    df = trade['df']

    # Risk & position sizing
    atr = trailing_sl_manager._calculate_atr(df)
    stop_loss_pips = max(1, round(atr * ATR_SL_MULTIPLIER))
    volume = risk_manager.position_size(symbol, stop_loss_pips)
    risk_amount = stop_loss_pips * 10 * volume

    if volume <= 0:
        return

    allowed, reason = trade_gatekeeper.authorize_trade(symbol, risk_amount)
    if not allowed:
        logger.warning(f"{symbol}: trade blocked — {reason}")
        return

    # Dry-run / Replay
    if DRY_RUN or REPLAY_MODE:
        logger.info(f"{symbol}: DRY-RUN | {side.upper()} | vol={volume}")
        stats_manager.stats[symbol]["trades"] += 1
        return

    # Execute order
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
        # Retraining logic can be added here if needed
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
# MAIN ORCHESTRATOR
# =========================================================
def start_master_orchestrator():
    logger.info("🚀 Starting FundedNext Live Orchestrator")

    mt5_readiness_check()
    StartupValidator().validate_or_die()

    logger.info(f"Environment set to: {ENVIRONMENT.upper()}")
    logger.info(f"Account Phase set to: {ACCOUNT_PHASE.upper()}")

    execution_flags = ExecutionFlags(
        account_phase=AccountPhase[ACCOUNT_PHASE],
        execution_mode=ExecutionMode[EXECUTION_MODE],
        ml_mode=MLMode[ML_MODE],
    )

    risk_manager = RiskManager()
    session_filter = SessionFilter()
    correlation_manager = CorrelationManager()
    trade_selector = TradeSelector(correlation_manager)
    trade_gatekeeper = TradeGatekeeper(execution_flags, risk_manager, session_filter)
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

            # Phase 1: Signal Generation
            potential_trades = []
            threads = []
            for symbol in ALLOWED_SYMBOLS:
                t = threading.Thread(
                    target=signal_generation_worker,
                    args=(
                        symbol,
                        feed,
                        signal_engine,
                        ml_router,
                        stats_manager,
                        execution_flags,
                        potential_trades,
                    ),
                )
                t.start()
                threads.append(t)
                time.sleep(PER_SYMBOL_THROTTLE)

            for t in threads:
                t.join()

            # Phase 2: Trade Selection
            selected_trades = trade_selector.select_best_trades(potential_trades)

            # Phase 3: Trade Execution
            for trade in selected_trades:
                trade_execution_worker(
                    trade,
                    risk_manager,
                    trade_gatekeeper,
                    order_router,
                    trailing_sl_manager,
                    execution_flags,
                    stats_manager,
                )

            # Manage open positions
            for symbol in ALLOWED_SYMBOLS:
                df = feed.get_candles(symbol, mt5.TIMEFRAME_M1, TIMEFRAME_BARS)
                if df is not None and not df.empty:
                    partial_tp_manager.manage(symbol, df)
                    trailing_sl_manager.manage(symbol, df)

            time.sleep(LOOP_SLEEP_SECONDS)

    except KeyboardInterrupt:
        logger.warning("🛑 Manual shutdown")

    finally:
        feed.shutdown()
        logger.info("Orchestrator shutdown complete")

# =========================================================
# ENTRY POINT
# =========================================================
if __name__ == "__main__":
    start_master_orchestrator()
