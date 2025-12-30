"""
signal_engine.py

Rule-based signal engine for FundedNext strategy.
Supports momentum + mean-reversion logic and regime detection.
"""

import pandas as pd
import numpy as np
from fundednext_trading_system.monitoring.logger import logger
from fundednext_trading_system.trading_core.news_sentiment import NewsSentiment

class SignalEngine:
    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold
        self.news_sentiment = NewsSentiment()

    def prepare_features(self, df: pd.DataFrame, regime: str = "range") -> pd.DataFrame:
        """
        Extract features for ML inference.
        Includes regime info and basic price/momentum features.
        """
        features = pd.DataFrame()
        features['close'] = df['close']
        features['high'] = df['high']
        features['low'] = df['low']
        features['open'] = df['open']

        # Moving averages
        features['ma5'] = df['close'].rolling(5).mean()
        features['ma20'] = df['close'].rolling(20).mean()
        features['ma50'] = df['close'].rolling(50).mean()

        # Momentum indicators
        features['momentum5'] = df['close'] - df['close'].shift(5)
        features['momentum20'] = df['close'] - df['close'].shift(20)

        # Regime indicator (trend=1, range=0)
        features['regime'] = 1 if regime == "trend" else 0

        # Volatility
        features['volatility'] = df['close'].rolling(20).std()

        features = features.fillna(0)
        return features

    def generate_signal(self, df: pd.DataFrame, symbol: str, regime: str = "range") -> tuple | None:
        """
        Rule-based fallback signal.
        Returns (side, confidence)
        """
        try:
            sentiment_score = self.news_sentiment.get_sentiment(symbol)
            last_close = df['close'].iloc[-1]
            ma5 = df['close'].rolling(5).mean().iloc[-1]
            ma20 = df['close'].rolling(20).mean().iloc[-1]
            ma50 = df['close'].rolling(50).mean().iloc[-1]

            # Trend regime logic
            if regime == "trend":
                if ma5 > ma20 > ma50:
                    confidence = 0.8 + (sentiment_score * 0.2)
                    return ("buy", confidence)
                elif ma5 < ma20 < ma50:
                    confidence = 0.8 - (sentiment_score * 0.2)
                    return ("sell", confidence)

            # Range regime logic (mean-reversion)
            else:
                if last_close > ma20:
                    confidence = 0.7 - (sentiment_score * 0.2)
                    return ("sell", confidence)
                elif last_close < ma20:
                    confidence = 0.7 + (sentiment_score * 0.2)
                    return ("buy", confidence)

            return None

        except Exception as e:
            logger.error(f"{symbol}: SignalEngine failed | {e}")
            return None
