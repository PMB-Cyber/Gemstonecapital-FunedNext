import os

BASE = "fundednext_trading_system"

STRUCTURE = [
    "bootstrap",
    "config",
    "trading_core",
    "execution",
    "ml",
    "data/historical",
    "data/live",
    "models/latest",
    "logs",
    "notebooks"
]

FILES = {
    "config/allowed_symbols.py": """ALLOWED_SYMBOLS = {
    "EURUSD","GBPUSD","USDJPY","XAUUSD","US30","NAS100"
}
""",

    "config/fundednext_rules.py": """ACCOUNT_BALANCE = 5000
DAILY_LOSS_LIMIT = 200
MAX_LOSS_LIMIT = 400
MAX_RISK_PER_TRADE = 50
MIN_TRADING_DAYS = 5
""",

    "config/sessions.py": """LONDON = (7, 16)
NEW_YORK = (13, 22)
""",

    "config/symbols_config.py": """SYMBOLS_CONFIG = {
    "EURUSD": {"ema_fast":21,"ema_slow":50,"atr_period":14,"rsi_period":14,"volatility_filter_threshold":1.2},
    "GBPUSD": {"ema_fast":22,"ema_slow":50,"atr_period":14,"rsi_period":14,"volatility_filter_threshold":1.25},
    "USDJPY": {"ema_fast":20,"ema_slow":50,"atr_period":14,"rsi_period":14,"volatility_filter_threshold":1.1},
    "XAUUSD": {"ema_fast":21,"ema_slow":50,"atr_period":14,"rsi_period":14,"volatility_filter_threshold":1.5},
    "US30":  {"ema_fast":21,"ema_slow":50,"atr_period":14,"rsi_period":14,"volatility_filter_threshold":1.6},
    "NAS100":{"ema_fast":20,"ema_slow":50,"atr_period":14,"rsi_period":14,"volatility_filter_threshold":1.45},
}
""",

    "trading_core/session_filter.py": """from datetime import datetime
from config.sessions import LONDON, NEW_YORK

def is_within_session():
    h = datetime.utcnow().hour
    return LONDON[0] <= h <= LONDON[1] or NEW_YORK[0] <= h <= NEW_YORK[1]
""",

    "trading_core/risk_manager.py": """from config.fundednext_rules import *

class RiskManager:
    def __init__(self):
        self.daily_loss = 0
        self.total_loss = 0

    def can_open_trade(self, risk):
        if risk > MAX_RISK_PER_TRADE:
            return False
        if self.daily_loss + risk > DAILY_LOSS_LIMIT:
            return False
        if self.total_loss + risk > MAX_LOSS_LIMIT:
            return False
        return True
""",

    "trading_core/signal_engine.py": """from ml.model_loader import ModelLoader
from ml.feature_engineering import FeatureEngineer
from config.allowed_symbols import ALLOWED_SYMBOLS
from trading_core.session_filter import is_within_session

class SignalEngine:
    def __init__(self):
        self.loader = ModelLoader()
        self.fe = FeatureEngineer()

    def generate(self, df, symbol):
        if symbol not in ALLOWED_SYMBOLS:
            return None
        if not is_within_session():
            return None
        feats = self.fe.compute_features(df, symbol).dropna()
        if feats.empty:
            return None
        X = feats.iloc[-1:].values
        score = self.loader.predict(symbol, X)
        if score > 0.7: return "buy"
        if score < 0.3: return "sell"
        return None
""",

    "execution/mt5_executor.py": """import MetaTrader5 as mt5
from config.allowed_symbols import ALLOWED_SYMBOLS

class MT5Executor:
    def execute(self, symbol, signal):
        if symbol not in ALLOWED_SYMBOLS:
            return
        # execution logic
""",

    "ml/feature_engineering.py": """import pandas as pd

class FeatureEngineer:
    def compute_features(self, df, symbol):
        return df
""",

    "ml/model_loader.py": """import joblib

class ModelLoader:
    def predict(self, symbol, X):
        model = joblib.load(f"models/latest/{symbol}.pkl")
        return model.predict_proba(X)[0][1]
""",

    "ml/train_models.py": """# Runs on Google Colab only
""",

    "notebooks/colab_training.ipynb": "{}",

    "main.py": """from trading_core.signal_engine import SignalEngine
from execution.mt5_executor import MT5Executor

print("System Ready")
""",

    "requirements.txt": """pandas
numpy
scikit-learn
joblib
MetaTrader5
loguru
"""
}

def generate():
    for d in STRUCTURE:
        os.makedirs(os.path.join(BASE, d), exist_ok=True)
    for path, content in FILES.items():
        with open(os.path.join(BASE, path), "w") as f:
            f.write(content)
    print("✅ FundedNext Production System Generated")

if __name__ == "__main__":
    generate()
