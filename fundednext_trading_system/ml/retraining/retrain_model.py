import os
import pandas as pd
import joblib
import numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier

from monitoring.logger import logger
from ml.monte_carlo_validator import MonteCarloValidator
from trading_core.model_guard import promote_model_version


# =========================
# CONFIG
# =========================
FEATURES = [
    "ema_diff",
    "atr",
    "rsi",
    "volume_norm",
    "volatility_regime",
    "trend",
]

MODEL_DIR = "models/candidates"
ACTIVE_MODEL_DIR = "models/active"

MIN_SAMPLES = 500
MIN_TRADES = 120
PROBA_LONG = 0.6
PROBA_SHORT = 0.4

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(ACTIVE_MODEL_DIR, exist_ok=True)


# =========================
# RETRAIN PIPELINE
# =========================
def retrain(symbol: str) -> dict:
    logger.info(f"🔁 Retraining model for {symbol}")

    old_path = f"ml/training/{symbol}_dataset.csv"
    new_path = f"ml/retraining/{symbol}_new_data.csv"

    if not os.path.exists(old_path) or not os.path.exists(new_path):
        raise FileNotFoundError("Training or retraining data missing")

    old = pd.read_csv(old_path, index_col=0)
    new = pd.read_csv(new_path, index_col=0)

    combined = (
        pd.concat([old, new])
        .drop_duplicates()
        .dropna()
        .reset_index(drop=True)
    )

    if len(combined) < MIN_SAMPLES:
        raise RuntimeError("❌ Insufficient data for retraining")

    X = combined[FEATURES]
    y = combined["target"]

    # =========================
    # TRAIN MODEL
    # =========================
    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        min_samples_leaf=30,
        random_state=42,
        n_jobs=-1,
    )

    model.fit(X, y)

    # =========================
    # BUILD RETURNS
    # =========================
    proba = model.predict_proba(X)[:, 1]
    returns = _build_trade_returns(proba, y)

    if len(returns) < MIN_TRADES:
        raise RuntimeError(
            f"❌ Insufficient trades generated: {len(returns)}"
        )

    # =========================
    # MONTE CARLO VALIDATION
    # =========================
    logger.info("📊 Running Monte Carlo validation")

    validator = MonteCarloValidator(
        simulations=5000,
        min_sharpe=0.8,
        max_risk_of_ruin=0.25,
    )

    report = validator.run(returns)

    if not report["passed"]:
        logger.critical(
            f"❌ MODEL REJECTED — Sharpe={report['sharpe_ratio']:.2f}, "
            f"RoR={report['risk_of_ruin']:.2f}"
        )
        raise RuntimeError("Model rejected by Monte Carlo gate")

    # =========================
    # SAVE + PROMOTE
    # =========================
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    model_path = f"{MODEL_DIR}/{symbol}_{timestamp}.pkl"

    joblib.dump(model, model_path)
    promote_model_version(symbol, model_path)

    logger.success(
        f"✅ MODEL PROMOTED | {symbol} | "
        f"Sharpe={report['sharpe_ratio']:.2f} | "
        f"RoR={report['risk_of_ruin']:.2f}"
    )

    return report


# =========================
# HELPERS
# =========================
def _build_trade_returns(proba: np.ndarray, target: pd.Series) -> np.ndarray:
    """
    Converts predictions into normalized trade returns
    suitable for Monte Carlo simulation.
    """
    returns = []

    for p, t in zip(proba, target):
        if p >= PROBA_LONG:
            returns.append(0.01 if t == 1 else -0.01)
        elif p <= PROBA_SHORT:
            returns.append(0.01 if t == 0 else -0.01)

    return np.array(returns, dtype=np.float32)
