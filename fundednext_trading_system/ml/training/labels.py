import numpy as np
import pandas as pd


def generate_labels(df, horizon=5, threshold=0.0003):
    future_close = df["close"].shift(-horizon)
    returns = (future_close - df["close"]) / df["close"]

    labels = (returns > threshold).astype(int)
    return labels
