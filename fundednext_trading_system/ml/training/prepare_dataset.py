import MetaTrader5 as mt5
from fundednext_trading_system.execution.mt5_data_feed import MT5DataFeed
from fundednext_trading_system.ml.feature_engineering import FeatureEngineer
import pandas as pd
import sys
from loguru import logger

LOOKAHEAD_BARS = 5
RETURN_THRESHOLD = 0.0002  # conservative

def prepare(symbol):
    feed = MT5DataFeed()
    fe = FeatureEngineer()

    df = feed.get_candles(symbol, mt5.TIMEFRAME_M1, 6000)

    if df is None or df.empty:
        logger.error(f"No data for {symbol}")
        return

    features = fe.compute_features(df, symbol).dropna()

    future_return = (
        df["close"].shift(-LOOKAHEAD_BARS) - df["close"]
    ) / df["close"]

    features["target"] = (future_return > RETURN_THRESHOLD).astype(int)
    features.dropna(inplace=True)

    out = f"ml/training/{symbol}_dataset.csv"
    features.to_csv(out)

    logger.success(f"{symbol} dataset saved → {out}")

    feed.shutdown()

if __name__ == "__main__":
    symbol = sys.argv[1]
    prepare(symbol)
