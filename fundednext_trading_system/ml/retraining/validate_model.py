import pandas as pd
import joblib
import numpy as np
from sklearn.metrics import accuracy_score, classification_report
from loguru import logger

FEATURES = [
    "ema_diff",
    "atr",
    "rsi",
    "volume_norm",
    "volatility_regime",
    "trend",
]

def validate(symbol):
    data = pd.read_csv(f"ml/training/{symbol}_dataset.csv", index_col=0)
    model = joblib.load(f"models/latest/{symbol}.pkl")

    X = data[FEATURES]
    y = data["target"]

    preds = model.predict(X)
    probs = model.predict_proba(X)[:, 1]

    acc = accuracy_score(y, preds)
    avg_prob = np.mean(probs)

    logger.info(f"MODEL VALIDATION — {symbol}")
    logger.info(f"Accuracy: {acc:.4f}")
    logger.info(f"Avg Confidence: {avg_prob:.4f}")
    logger.info(classification_report(y, preds))

    if acc < 0.52:
        raise RuntimeError(f"Model for {symbol} FAILED validation")

    logger.success(f"{symbol} model PASSED validation")
