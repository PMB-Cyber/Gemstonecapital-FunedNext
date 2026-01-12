import pandas as pd
from datetime import datetime
import dukascopy_python as duka
from fundednext_trading_system.monitoring.logger import logger
import time

class DukascopyDataFeed:
    DUKASCOPY_SYMBOL_MAP = {
        "EURUSD": "eurusd", "GBPUSD": "gbpusd", "USDJPY": "usdjpy", "XAUUSD": "xauusd", "US30": "usa30", "NDX100": "nas100",
        "AUDCAD": "audcad", "AUDCHF": "audchf", "AUDJPY": "audjpy", "AUDNZD": "audnzd", "CADJPY": "cadjpy", "CHFJPY": "chfjpy",
        "EURAUD": "euraud", "EURCAD": "eurcad", "EURCHF": "eurchf", "EURGBP": "eurgbp", "EURJPY": "eurjpy", "GBPAUD": "gbpaud",
        "GBPJPY": "gbpjpy", "NZDUSD": "nzdusd", "USDCAD": "usdcad", "USDCHF": "usdchf", "GER30": "deu40", "UK100": "uk100",
        "SPX500": "usa500", "XAGUSD": "xagusd"
    }

    def get_candles(self, symbol, timeframe_in_seconds, count, end_date=None, max_retries=3, backoff_factor=2):
        """
        Fetches historical candle data from Dukascopy using the duka library,
        with a retry mechanism and exponential backoff.
        """
        dukascopy_symbol = self.DUKASCOPY_SYMBOL_MAP.get(symbol)
        if not dukascopy_symbol:
            logger.error(f"Unsupported symbol: {symbol}")
            return None

        start_date = datetime(2024, 1, 1)
        if end_date is None:
            end_date = datetime.now()

        retries = 0
        while retries < max_retries:
            try:
                logger.info(f"Fetching tick data for {dukascopy_symbol} from {start_date} to {end_date}...")
                df = duka.fetch(
                    dukascopy_symbol,
                    duka.INTERVAL_TICK,
                    duka.OFFER_SIDE_BID,
                    start_date,
                    end_date,
                )

                if df is None or df.empty:
                    raise ValueError("Received empty or None DataFrame from Dukascopy.")

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
                retries += 1
                wait_time = backoff_factor ** retries
                logger.warning(f"Attempt {retries}/{max_retries} failed for {symbol}: {e}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

        logger.error(f"Failed to fetch data for {symbol} after {max_retries} attempts.")
        return None
