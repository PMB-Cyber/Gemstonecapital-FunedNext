import MetaTrader5 as mt5
from fundednext_trading_system.execution.mt5_data_feed import MT5DataFeed
from fundednext_trading_system.ml.feature_engineering import FeatureEngineer
import pandas as pd

def collect(symbol, bars=3000):
    feed = MT5DataFeed()
    fe = FeatureEngineer()

    df = feed.get_candles(symbol, mt5.TIMEFRAME_M1, bars)
    features = fe.compute_features(df, symbol).dropna()

    features.to_csv(f"ml/retraining/{symbol}_new_data.csv")
    feed.shutdown()
