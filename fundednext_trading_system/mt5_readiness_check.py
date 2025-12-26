import MetaTrader5 as mt5
from config.allowed_symbols import ALLOWED_SYMBOLS

TIMEFRAME = mt5.TIMEFRAME_M1
CANDLE_COUNT = 10

def check_mt5_connection():
    if not mt5.initialize():
        raise RuntimeError(f"MT5 initialize() failed, error code={mt5.last_error()}")
    print("✅ MT5 initialized successfully")

def check_symbols():
    print("\n🔹 Checking allowed symbols...")
    all_ok = True
    for symbol in ALLOWED_SYMBOLS:
        info = mt5.symbol_info(symbol)
        if info is None:
            print(f"❌ Symbol not found in MT5: {symbol}")
            all_ok = False
            continue
        if not info.visible:
            print(f"⚠️ Symbol not visible in MT5: {symbol}")
        print(f"✅ {symbol} found | tick={info.bid:.5f}/{info.ask:.5f} | spread={info.spread}")
    return all_ok

def check_candles():
    print("\n🔹 Checking candle data...")
    all_ok = True
    for symbol in ALLOWED_SYMBOLS:
        rates = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, CANDLE_COUNT)
        if rates is None or len(rates) == 0:
            print(f"❌ No candle data for {symbol}")
            all_ok = False
        else:
            print(f"✅ {symbol} | {len(rates)} candles retrieved | last close={rates[-1][4]:.5f}")
    return all_ok

def main():
    try:
        check_mt5_connection()
        symbols_ok = check_symbols()
        candles_ok = check_candles()

        if symbols_ok and candles_ok:
            print("\n🎯 All checks passed. Ready for live trading!")
        else:
            print("\n⚠️ Some checks failed. Resolve issues before live trading.")

    finally:
        mt5.shutdown()
        print("ℹ️ MT5 connection closed")

if __name__ == "__main__":
    main()
