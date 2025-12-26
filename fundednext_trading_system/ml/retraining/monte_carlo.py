import pandas as pd
import numpy as np
import joblib
from loguru import logger

FEATURES = [
    "ema_diff","atr","rsi",
    "volume_norm","volatility_regime","trend"
]

def monte_carlo_test(symbol, runs=200):
    data = pd.read_csv(f"ml/training/{symbol}_dataset.csv", index_col=0)
    model = joblib.load(f"models/latest/{symbol}.pkl")

    results = []

    for _ in range(runs):
        sample = data.sample(frac=0.8, replace=True)
        X = sample[FEATURES]
        y = sample["target"]

        preds = model.predict(X)
        acc = (preds == y).mean()
        results.append(acc)

    mean_acc = np.mean(results)
    std_acc = np.std(results)

    logger.info(f"MONTE CARLO — {symbol}")
    logger.info(f"Mean Accuracy: {mean_acc:.4f}")
    logger.info(f"Std Dev: {std_acc:.4f}")

    if mean_acc < 0.52 or std_acc > 0.05:
        raise RuntimeError(f"{symbol} FAILED Monte Carlo robustness")

    logger.success(f"{symbol} PASSED Monte Carlo")
