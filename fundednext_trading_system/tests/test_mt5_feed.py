from execution.mt5_data_feed import MT5DataFeed

feed = MT5DataFeed()
df = feed.get_candles("EURUSD", bars=100)

print(df.tail())
feed.shutdown()
