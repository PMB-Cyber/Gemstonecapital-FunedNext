import MetaTrader5 as mt5
from execution.mt5_data_feed import MT5DataFeed

feed = MT5DataFeed()
df = feed.get_candles("EURUSD", mt5.TIMEFRAME_M1, count=100)

print(df.tail())
feed.shutdown()
