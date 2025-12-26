import time
from datetime import datetime, timedelta
import pandas as pd
import MetaTrader5 as mt5

from config.allowed_symbols import ALLOWED_SYMBOLS
from monitoring.logger import logger
from trading_core.risk_manager import RiskManager
from trading_core.capital_scaler import CapitalScaler
from trading_core.signal_engine import SignalEngine
from trading_core.execution_flags import ExecutionFlags, AccountPhase, ExecutionMode, MLMode

# =========================
# DRY RUN REPORTER
# =========================
class DryRunReporter:
    """
    Simulates trading for N hours without sending live orders.
    Useful for verifying risk, scaling, and ML signals.
    """

    def __init__(self, duration_hours: float = 24.0):
        self.duration_hours = duration_hours
        self.start_time = datetime.utcnow()

        self.execution_flags = ExecutionFlags(
            account_phase=AccountPhase.CHALLENGE,
            execution_mode=ExecutionMode.SHADOW,
            ml_mode=MLMode.TRAINING
        )

        self.risk_manager = RiskManager()
        self.scaler = CapitalScaler(self.risk_manager.start_balance)
        self.signal_engine = SignalEngine(confidence_threshold=0.7)

        if not mt5.initialize():
            raise RuntimeError("MT5 initialization failed")

        logger.info("🧪 DryRunReporter initialized")

    # =========================
    # CANDLE DATA FETCH
    # =========================
    def _get_candles(self, symbol: str, n_bars: int = 300):
        """Fetches recent M5 candles from MT5."""
        if not mt5.symbol_select(symbol, True):
            logger.warning(f"{symbol}: symbol not selectable")
            return None

        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, n_bars)
        if rates is None or len(rates) == 0:
            logger.error(f"{symbol}: no candle data")
            return None

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    # =========================
    # SIMULATION LOOP
    # =========================
    def run(self):
        logger.info(f"🧪 Starting {self.duration_hours}h DRY RUN simulation")
        end_time = self.start_time + timedelta(hours=self.duration_hours)

        try:
            while datetime.utcnow() < end_time:
                for symbol in ALLOWED_SYMBOLS:
                    df = self._get_candles(symbol)
                    if df is None or df.empty:
                        continue

                    # Prepare features for ML signal
                    features = self.signal_engine.prepare_features(df)
                    ml_signal = features  # placeholder for ML inference

                    # Mock ATR-based stop loss
                    stop_loss_pips = max(1, 10)
                    volume = self.risk_manager.position_size(symbol, stop_loss_pips)
                    risk_amount = stop_loss_pips * 10 * volume

                    if volume <= 0 or not self.risk_manager.can_open_trade(risk_amount):
                        continue

                    logger.info(
                        f"[DryRun] {symbol} | volume={volume} | risk=${risk_amount:.2f}"
                    )

                    # Simulate profit/loss randomly
                    import random
                    pnl = random.choice([-risk_amount, risk_amount * 0.5])
                    if pnl < 0:
                        self.risk_manager.register_loss(-pnl)
                    else:
                        self.risk_manager.register_profit(pnl)

                # Short sleep to prevent MT5 hammering
                time.sleep(1)

        except KeyboardInterrupt:
            logger.warning("🛑 Dry run interrupted manually")

        finally:
            mt5.shutdown()
            logger.info("✅ Dry run simulation complete")
            logger.info(
                f"Final Daily Loss=${self.risk_manager.daily_loss:.2f} | "
                f"Total Loss=${self.risk_manager.total_loss:.2f}"
            )


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    reporter = DryRunReporter(duration_hours=0.1)  # quick test run
    reporter.run()
