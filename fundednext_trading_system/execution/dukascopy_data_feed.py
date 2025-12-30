import subprocess
import pandas as pd
from datetime import datetime, timedelta
from fundednext_trading_system.monitoring.logger import logger

class DukascopyDataFeed:
    TIMEFRAME_MAP = {
        60: "M1",
        300: "M5",
        900: "M15",
        1800: "M30",
        3600: "H1",
        14400: "H4",
        86400: "D1",
    }

    def get_candles(self, symbol, timeframe_in_seconds, count):
        """
        Fetches historical candle data from Dukascopy.
        """
        timeframe_str = self.TIMEFRAME_MAP.get(timeframe_in_seconds)
        if not timeframe_str:
            logger.warning(f"Unsupported timeframe: {timeframe_in_seconds} seconds. Defaulting to M5.")
            timeframe_str = "M5"

        end_date = datetime.utcnow()
        days_to_fetch = (count * timeframe_in_seconds) / (24 * 3600) + 1
        start_date = end_date - timedelta(days=days_to_fetch)

        command = [
            "dukascopy",
            symbol,
            "-s", start_date.strftime('%Y-%m-%d'),
            "-e", end_date.strftime('%Y-%m-%d'),
            "-c", timeframe_str,
            "--header",
        ]

        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                logger.error(f"Error fetching data from Dukascopy: {stderr.decode()}")
                return None

            from io import StringIO
            data = StringIO(stdout.decode())
            df = pd.read_csv(data)
            df.rename(columns={'timestamp': 'time', 'volume': 'tick_volume'}, inplace=True)
            return df.tail(count)

        except FileNotFoundError:
            logger.error("The 'dukascopy' command-line tool is not installed or not in the system's PATH.")
            return None
