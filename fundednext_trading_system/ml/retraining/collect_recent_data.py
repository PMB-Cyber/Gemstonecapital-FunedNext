from execution.mt5_data_feed import MT5DataFeed
from ml.feature_engineering import FeatureEngineer
import pandas as pd

def collect(symbol, bars=3000):
    feed = MT5DataFeed()
    fe = FeatureEngineer()

    df = feed.get_candles(symbol, bars=bars)
    features = fe.compute_features(df, symbol).dropna()

    features.to_csv(f"ml/retraining/{symbol}_new_data.csv")
    feed.shutdown()
