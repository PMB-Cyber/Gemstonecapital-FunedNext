import pandas as pd
import numpy as np
from fundednext_trading_system.config.symbols_config import SYMBOLS_CONFIG
from loguru import logger


class FeatureEngineer:
    def compute_features(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        if symbol not in SYMBOLS_CONFIG:
            logger.error(f"No symbol config found for {symbol}")
            return pd.DataFrame()

        cfg = SYMBOLS_CONFIG[symbol]
        df = df.copy()

        # EMA
        df["ema_fast"] = df["close"].ewm(span=cfg["ema_fast"], adjust=False).mean()
        df["ema_slow"] = df["close"].ewm(span=cfg["ema_slow"], adjust=False).mean()
        df["ema_diff"] = df["ema_fast"] - df["ema_slow"]

        # ATR
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift()).abs()
        low_close = (df["low"] - df["close"].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df["atr"] = tr.rolling(cfg["atr_period"]).mean()

        # RSI
        delta = df["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(cfg["rsi_period"]).mean()
        avg_loss = loss.rolling(cfg["rsi_period"]).mean()
        rs = avg_gain / avg_loss
        df["rsi"] = 100 - (100 / (1 + rs))

        # Volume normalization
        df["volume_norm"] = df["tick_volume"] / df["tick_volume"].rolling(20).mean()

        # Volatility regime
        df["volatility_regime"] = (
            df["atr"] > df["atr"].rolling(20).mean() * cfg["volatility_filter_threshold"]
        ).astype(int)

        # Trend direction
        df["trend"] = np.sign(df["ema_diff"])

        # Final clean feature set
        features = df[
            [
                "ema_diff",
                "atr",
                "rsi",
                "volume_norm",
                "volatility_regime",
                "trend",
            ]
        ]

        return features
