import pandas as pd
from datetime import datetime
import dukascopy_python as duka
from fundednext_trading_system.monitoring.logger import logger

class DukascopyDataFeed:
    DUKASCOPY_SYMBOL_MAP = {
        "EURUSD": "eurusd",
        "GBPUSD": "gbpusd",
        "USDJPY": "usdjpy",
        "XAUUSD": "xauusd",
        "US30": "usa30idx",
        "NDX100": "nas100idx",
    }

    def get_candles(self, symbol, timeframe_in_seconds, count):
        """
        Fetches historical candle data from Dukascopy using the duka library.
        """
        dukascopy_symbol = self.DUKASCOPY_SYMBOL_MAP.get(symbol)
        if not dukascopy_symbol:
            logger.error(f"Unsupported symbol: {symbol}")
            return None

        start_date = datetime(2024, 1, 1)
        end_date = datetime(2026, 12, 31)

        try:
            logger.info(f"Fetching tick data for {dukascopy_symbol} from {start_date} to {end_date}...")
            df = duka.fetch(
                dukascopy_symbol,
                duka.INTERVAL_TICK,
                duka.OFFER_SIDE_BID,
                start_date,
                end_date,
            )
            logger.success(f"Successfully fetched {len(df)} ticks for {dukascopy_symbol}.")

            # Resample tick data to OHLC candles
            rule = f'{timeframe_in_seconds}s'

            # Resample OHLC data
            ohlc = df['bidPrice'].resample(rule).ohlc()

            # Resample volume data
            volume = df['bidVolume'].resample(rule).sum()

            # Combine OHLC and volume data
            resampled_df = pd.concat([ohlc, volume], axis=1).ffill()

            # Rename columns to match the expected format
            resampled_df.rename(columns={'bidVolume': 'tick_volume'}, inplace=True)

            # Reset index to make 'time' a column
            resampled_df.reset_index(inplace=True)
            resampled_df.rename(columns={'timestamp': 'time'}, inplace=True)

            return resampled_df.tail(count)

        except Exception as e:
            logger.error(f"Error fetching data from Dukascopy: {e}")
            return None
