import MetaTrader5 as mt5

mt5.initialize()

symbols = ["EURUSD","GBPUSD","USDJPY","XAUUSD","US30","NDX100"]
for s in symbols:
    mt5.symbol_select(s, True)
    rates = mt5.copy_rates_from_pos(s, mt5.TIMEFRAME_M5, 0, 10)
    print(s, 0 if rates is None else len(rates))

mt5.shutdown()
