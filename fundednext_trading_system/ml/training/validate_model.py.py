import joblib
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

def validate(symbol="EURUSD"):
    model = joblib.load(f"models/latest/{symbol}.pkl")
    data = pd.read_csv(f"ml/training/{symbol}_dataset.csv", index_col=0)

    X = data[[
        "ema_diff",
        "atr",
        "rsi",
        "volume_norm",
        "volatility_regime",
        "trend"
    ]]
    y = data["target"]

    preds = model.predict(X)
    probs = model.predict_proba(X)[:, 1]

    print(f"\n=== VALIDATION REPORT FOR {symbol} ===\n")
    print(classification_report(y, preds))
    print("Confusion Matrix:")
    print(confusion_matrix(y, preds))
    print("\nAverage confidence:", probs.mean())

if __name__ == "__main__":
    validate()
