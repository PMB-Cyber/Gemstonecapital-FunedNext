import time
from collections import defaultdict
from datetime import datetime, timedelta

from fundednext_trading_system.config.allowed_symbols import ALLOWED_SYMBOLS
from fundednext_trading_system.monitoring.logger import logger
from fundednext_trading_system.trading_core.signal_engine import SignalEngine
from fundednext_trading_system.trading_core.risk_manager import RiskManager
from fundednext_trading_system.trading_core.trade_gatekeeper import TradeGatekeeper
from fundednext_trading_system.execution.mt5_data_feed import MT5DataFeed


class DryRunReporter:
    def __init__(
        self,
        duration_hours: int = 24,
        bars: int = 300,
    ):
        self.duration = timedelta(hours=duration_hours)
        self.bars = bars

        self.stats = defaultdict(int)

        self.feed = MT5DataFeed()
        self.signal_engine = SignalEngine(confidence_threshold=0.7)
        self.risk_manager = RiskManager()

    # =========================
    # MAIN
    # =========================

    def run(self):
        logger.info("🧪 Starting 24h DRY RUN simulation")

        start = datetime.utcnow()
        end = start + self.duration

        while datetime.utcnow() < end:
            for symbol in ALLOWED_SYMBOLS:
                df = self.feed.get_candles(symbol, mt5.TIMEFRAME_M1, self.bars)
                if df is None or len(df) < 50:
                    continue

                signal = self.signal_engine.generate_signal(df, symbol)
                if not signal:
                    self.stats["no_signal"] += 1
                    continue

                side, score = signal
                self.stats["signals"] += 1

                risk = self.risk_manager.estimate_trade_risk(
                    symbol, stop_loss_pips=10
                )

                if not self.risk_manager.validate_trade_risk(risk):
                    self.stats["risk_blocked"] += 1
                    continue

                self.stats["approved"] += 1

            time.sleep(60)

        self.report()

    # =========================
    # REPORT
    # =========================

    def report(self):
        logger.info("📊 DRY RUN REPORT")
        for k, v in self.stats.items():
            logger.info(f"{k}: {v}")
