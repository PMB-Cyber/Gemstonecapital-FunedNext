import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
from fundednext_trading_system.monitoring.logger import logger
import time

class YFinanceDataFeed:
    YFINANCE_SYMBOL_MAP = {
        # Forex
        "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", "USDJPY": "USDJPY=X",
        "AUDCAD": "AUDCAD=X", "AUDCHF": "AUDCHF=X", "AUDJPY": "AUDJPY=X",
        "AUDNZD": "AUDNZD=X", "CADJPY": "CADJPY=X", "CHFJPY": "CHFJPY=X",
        "EURAUD": "EURAUD=X", "EURCAD": "EURCAD=X", "EURCHF": "EURCHF=X",
        "EURGBP": "EURGBP=X", "EURJPY": "EURJPY=X", "GBPAUD": "GBPAUD=X",
        "GBPJPY": "GBPJPY=X", "NZDUSD": "NZDUSD=X", "USDCAD": "USDCAD=X",
        "USDCHF": "USDCHF=X",
        # Commodities
        "XAUUSD": "GC=F", "XAGUSD": "SI=F",
        # Indices
        "US30": "YM=F", "NDX100": "NQ=F", "GER30": "^GDAXI", "UK100": "^FTSE", "SPX500": "ES=F"
    }

    def _timeframe_to_interval(self, timeframe_in_seconds):
        """Converts timeframe in seconds to yfinance interval string."""
        if timeframe_in_seconds == 86400:
            return "1d"
        minutes = timeframe_in_seconds // 60
        return f"{minutes}m"

    def get_candles(self, symbol, timeframe_in_seconds, count=None, start_date=None, end_date=None, max_retries=3, backoff_factor=2):
        """
        Fetches historical candle data from yfinance with retry mechanism.
        """
        yf_symbol = self.YFINANCE_SYMBOL_MAP.get(symbol)
        if not yf_symbol:
            logger.error(f"Unsupported symbol: {symbol}")
            return None

        interval = self._timeframe_to_interval(timeframe_in_seconds)

        retries = 0
        while retries < max_retries:
            try:
                logger.info(f"Fetching {interval} data for {yf_symbol} from {start_date.date()} to {end_date.date()}...")
                ticker = yf.Ticker(yf_symbol)
                df = ticker.history(
                    start=start_date,
                    end=end_date,
                    interval=interval,
                    auto_adjust=True
                )

                if df is None or df.empty:
                    raise ValueError("Received empty or None DataFrame from yfinance.")

                logger.success(f"Successfully fetched {len(df)} candles for {yf_symbol}.")

                # Rename columns to match the expected format
                df.rename(columns={
                    'Open': 'open',
                    'High': 'high',
                    'Low': 'low',
                    'Close': 'close',
                    'Volume': 'tick_volume'
                }, inplace=True)

                # Reset index to make 'time' a column
                df.reset_index(inplace=True)
                df.rename(columns={'Date': 'time', 'index': 'time'}, inplace=True)

                # Ensure 'time' column is timezone-aware (yfinance can be inconsistent)
                if df['time'].dt.tz is None:
                    df['time'] = df['time'].dt.tz_localize('UTC')

                # Clean data: forward-fill missing values, then drop any remaining NaNs
                df.ffill(inplace=True)
                df.dropna(inplace=True)

                if count:
                    return df.tail(count)
                return df

            except Exception as e:
                retries += 1
                wait_time = backoff_factor ** retries
                logger.warning(f"Attempt {retries}/{max_retries} failed for {symbol}: {e}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

        logger.error(f"Failed to fetch data for {symbol} after {max_retries} attempts.")
        return None
