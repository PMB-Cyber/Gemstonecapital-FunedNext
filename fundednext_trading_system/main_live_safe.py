import time

from monitoring.performance_tracker import record_signal, print_stats
from monitoring.discord_logger import broadcast
from execution.mt5_data_feed import MT5DataFeed
from trading_core.signal_engine import SignalEngine
from config.allowed_symbols import ALLOWED_SYMBOLS
from loguru import logger


# =========================
# SAFE MODE LOOP
# =========================
def run_safe_mode():
    feed = MT5DataFeed()
    engine = SignalEngine(confidence_threshold=0.7)

    logger.info("SAFE MODE started — signals only, no trading")
    broadcast("🟢 SAFE MODE started — signals only, no trading")

    try:
        while True:
            for symbol in ALLOWED_SYMBOLS:
                df = feed.get_candles(symbol, bars=300)

                if df is None or df.empty or len(df) < 50:
                    msg = f"{symbol}: insufficient data"
                    logger.warning(msg)
                    broadcast(msg)
                    continue

                signal = engine.generate_signal(df, symbol)

                if signal:
                    side, score = signal
                    record_signal(symbol, side, score)

                    msg = f"📈 SIGNAL {symbol} → {side.upper()} | score={score:.2f}"
                    logger.success(msg)
                    broadcast(msg)
                else:
                    msg = f"{symbol}: no valid signal"
                    logger.info(msg)
                    broadcast(msg)

            print_stats()
            broadcast("📊 Performance stats updated")

            time.sleep(60)  # 1-minute cadence (FundedNext safe)

    except KeyboardInterrupt:
        logger.warning("SAFE MODE stopped by user")
        broadcast("🛑 SAFE MODE stopped by user")

    except Exception as e:
        logger.exception(f"Runtime error: {e}")
        broadcast(f"🔥 Runtime error: {e}")
        time.sleep(30)

    finally:
        feed.shutdown()
        broadcast("🔌 MT5 data feed disconnected")


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    run_safe_mode()
