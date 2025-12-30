from fundednext_trading_system.config.settings import ENVIRONMENT
from fundednext_trading_system.monitoring.logger import logger

if ENVIRONMENT == "production":
    try:
        import MetaTrader5 as mt5
    except ImportError:
        logger.error("Failed to import MetaTrader5. Please ensure it's installed and you're on a Windows system.")
        mt5 = None
else:
    from fundednext_trading_system.MetaTrader5 import MetaTrader5 as mt5

class MT5DataFeed:
    def __init__(self):
        if not mt5 or not mt5.initialize():
            logger.error("❌ MT5 initialization failed")
            raise SystemExit("MT5 not initialized")

    def get_candles(self, symbol, timeframe, count):
        """Return recent candles as a DataFrame-like object."""
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        if rates is None:
            return None
        import pandas as pd
        df = pd.DataFrame(rates)
        return df

    def get_positions(self, symbol):
        """Return a list of open positions for the symbol."""
        positions = mt5.positions_get(symbol=symbol)
        return positions if positions else []

    def get_open_positions(self, symbol):
        """Alias for heartbeat usage."""
        return self.get_positions(symbol)

    def symbols(self):
        """Return all symbols being monitored."""
        return [s.name for s in mt5.symbols_get()]

    def shutdown(self):
        if mt5:
            mt5.shutdown()
