import pandas as pd
from datetime import datetime
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

    def get_candles(self, symbol, timeframe, count=None, start_pos=0, start_date=None, end_date=None):
        """Return recent candles as a DataFrame."""
        if start_date and end_date:
            rates = mt5.copy_rates_range(symbol, timeframe, start_date, end_date)
        elif count:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, start_pos, count)
        else:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 1000)

        if rates is None or len(rates) == 0:
            return None
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def get_ticks(self, symbol, count=10000, start_date=None, end_date=None):
        """Fetch raw tick data."""
        if start_date and end_date:
            ticks = mt5.copy_ticks_range(symbol, start_date, end_date, mt5.COPY_TICKS_ALL)
        else:
            ticks = mt5.copy_ticks_from(symbol, datetime.now(), count, mt5.COPY_TICKS_ALL)

        if ticks is None or len(ticks) == 0:
            return None
        df = pd.DataFrame(ticks)
        df['time'] = pd.to_datetime(df['time'], unit='s')
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

    def aggregate_ticks_to_m5(self, ticks_df):
        """Aggregates raw ticks into M5 candles."""
        if ticks_df is None or ticks_df.empty:
            return None

        # In Forex, 'last' price is often 0. Use (bid + ask) / 2 instead.
        if 'last' not in ticks_df.columns or (ticks_df['last'] == 0).all():
            ticks_df['price'] = (ticks_df['bid'] + ticks_df['ask']) / 2
        else:
            ticks_df['price'] = ticks_df['last']
            # Fallback for mixed cases
            zero_mask = (ticks_df['price'] == 0)
            if zero_mask.any():
                ticks_df.loc[zero_mask, 'price'] = (ticks_df.loc[zero_mask, 'bid'] + ticks_df.loc[zero_mask, 'ask']) / 2

        df = ticks_df.set_index('time')
        ohlc = df['price'].resample('5min').ohlc()
        volume = df['volume'].resample('5min').sum()

        res = pd.concat([ohlc, volume], axis=1)
        res.columns = ['open', 'high', 'low', 'close', 'tick_volume']
        return res.dropna().reset_index()
