import pandas as pd
import joblib
import os
import sys
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from loguru import logger

FEATURES = [
    "ema_diff",
    "atr",
    "rsi",
    "volume_norm",
    "volatility_regime",
    "trend",
]

def train(symbol):
    path = f"ml/training/{symbol}_dataset.csv"

    if not os.path.exists(path):
        logger.error(f"Dataset missing for {symbol}")
        return

    df = pd.read_csv(path, index_col=0)

    X = df[FEATURES]
    y = df["target"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        min_samples_leaf=50,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    acc = model.score(X_test, y_test)
    logger.success(f"{symbol} model accuracy: {acc:.3f}")

    os.makedirs("models/latest", exist_ok=True)
    out = f"models/latest/{symbol}.pkl"
    joblib.dump(model, out)

    logger.success(f"Model saved → {out}")

if __name__ == "__main__":
    symbol = sys.argv[1]
    train(symbol)
