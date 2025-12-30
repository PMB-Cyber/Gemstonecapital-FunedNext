import pandas as pd
import threading
from fundednext_trading_system.execution.dukascopy_data_feed import DukascopyDataFeed
from fundednext_trading_system.config.settings import ALLOWED_SYMBOLS, TIMEFRAME_BARS
from fundednext_trading_system.monitoring.logger import logger

class CorrelationManager:
    def __init__(self, days_back=30):
        self.data_feed = DukascopyDataFeed()
        self.correlation_matrix = None
        self.matrix_ready = False

        # Run calculation in a background thread
        thread = threading.Thread(target=self._calculate_correlation_matrix, args=(days_back,))
        thread.daemon = True
        thread.start()

    def _calculate_correlation_matrix(self, days_back):
        """
        Fetches historical data and computes the correlation matrix of returns.
        """
        logger.info("Calculating symbol correlation matrix in background...")
        all_prices = pd.DataFrame()

        candles_per_day = (24 * 3600) / TIMEFRAME_BARS
        count = int(candles_per_day * days_back)

        for symbol in ALLOWED_SYMBOLS:
            df = self.data_feed.get_candles(symbol, TIMEFRAME_BARS, count=count)
            if df is not None and not df.empty:
                # Assuming the 'time' column contains Unix timestamps
                df['time'] = pd.to_datetime(df['time'], unit='s')
                df.set_index('time', inplace=True)
                all_prices[symbol] = df['close']
            else:
                logger.warning(f"Could not fetch data for {symbol} for correlation matrix.")

        if all_prices.empty:
            logger.error("Could not fetch any data. Correlation matrix calculation failed.")
            return

        returns = all_prices.pct_change().dropna()
        self.correlation_matrix = returns.corr()
        self.matrix_ready = True
        logger.success("Correlation matrix calculated successfully.")
        logger.debug(f"\n{self.correlation_matrix}")


    def get_correlation(self, symbol1: str, symbol2: str) -> float:
        """
        Returns the correlation between two symbols.
        """
        if not self.matrix_ready or self.correlation_matrix is None:
            logger.warning("Correlation matrix not ready yet.")
            return 0.0

        if symbol1 not in self.correlation_matrix or symbol2 not in self.correlation_matrix:
            logger.warning(f"One or both symbols ({symbol1}, {symbol2}) not in correlation matrix.")
            return 0.0

        return self.correlation_matrix.loc[symbol1, symbol2]
