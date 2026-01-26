"""
signal_engine.py

Hybrid Signal Engine for FundedNext strategy.
Includes Mean Reversion, Momentum, Pullback, and Breakout strategies.
"""

import pandas as pd
import numpy as np
from ta.trend import ADXIndicator, EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from fundednext_trading_system.monitoring.logger import logger
from fundednext_trading_system.trading_core.news_sentiment import NewsSentiment
from fundednext_trading_system.config.symbols_config import SYMBOLS_CONFIG

class SignalEngine:
    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold
        self.news_sentiment = NewsSentiment()

    def detect_regime(self, df: pd.DataFrame) -> str:
        """
        Detects market regime: trend, range, or high_volatility.
        """
        if len(df) < 50:
            return "range"

        adx = ADXIndicator(df['high'], df['low'], df['close'], window=14).adx()
        current_adx = adx.iloc[-1]

        atr = AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()
        avg_atr = atr.rolling(50).mean()

        if current_adx > 25:
            return "trend"
        elif atr.iloc[-1] > avg_atr.iloc[-1] * 1.5:
            return "high_volatility"
        else:
            return "range"

    def prepare_features(self, df: pd.DataFrame, regime: str = "range") -> pd.DataFrame:
        """
        Extract features for ML inference.
        """
        features = pd.DataFrame(index=df.index)
        features['close'] = df['close']

        # Indicators
        features['rsi'] = RSIIndicator(df['close'], window=14).rsi()
        features['adx'] = ADXIndicator(df['high'], df['low'], df['close'], window=14).adx()

        ema20 = EMAIndicator(df['close'], window=20).ema_indicator()
        ema50 = EMAIndicator(df['close'], window=50).ema_indicator()
        features['ema_diff'] = ema20 - ema50

        bb = BollingerBands(df['close'], window=20, window_dev=2)
        features['bb_width'] = bb.bollinger_wband()
        features['bb_hi_diff'] = bb.bollinger_hband() - df['close']
        features['bb_lo_diff'] = df['close'] - bb.bollinger_lband()

        features['atr'] = AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()

        # Regime one-hot (simplified)
        features['is_trend'] = 1 if regime == "trend" else 0
        features['is_high_vol'] = 1 if regime == "high_volatility" else 0

        features = features.fillna(0)
        return features

    def _get_momentum_signal(self, df: pd.DataFrame, config: dict) -> tuple | None:
        adx = ADXIndicator(df['high'], df['low'], df['close'], window=14).adx().iloc[-1]
        ema_fast = EMAIndicator(df['close'], window=config['ema_fast']).ema_indicator().iloc[-1]
        ema_slow = EMAIndicator(df['close'], window=config['ema_slow']).ema_indicator().iloc[-1]

        if adx > 25:
            if ema_fast > ema_slow:
                return ("buy", 0.8)
            elif ema_fast < ema_slow:
                return ("sell", 0.8)
        return None

    def _get_mean_reversion_signal(self, df: pd.DataFrame, config: dict) -> tuple | None:
        rsi = RSIIndicator(df['close'], window=config['rsi_period']).rsi().iloc[-1]
        bb = BollingerBands(df['close'], window=20, window_dev=2)

        if rsi < 30 and df['close'].iloc[-1] < bb.bollinger_lband().iloc[-1]:
            return ("buy", 0.75)
        elif rsi > 70 and df['close'].iloc[-1] > bb.bollinger_hband().iloc[-1]:
            return ("sell", 0.75)
        return None

    def _get_pullback_signal(self, df: pd.DataFrame, config: dict) -> tuple | None:
        ema_fast = EMAIndicator(df['close'], window=config['ema_fast']).ema_indicator().iloc[-1]
        ema_slow = EMAIndicator(df['close'], window=config['ema_slow']).ema_indicator().iloc[-1]
        rsi = RSIIndicator(df['close'], window=config['rsi_period']).rsi().iloc[-1]

        # Uptrend pullback
        if ema_fast > ema_slow:
            if df['low'].iloc[-1] <= ema_fast and df['close'].iloc[-1] > ema_fast and rsi < 45:
                return ("buy", 0.85)
        # Downtrend pullback
        elif ema_fast < ema_slow:
            if df['high'].iloc[-1] >= ema_fast and df['close'].iloc[-1] < ema_fast and rsi > 55:
                return ("sell", 0.85)
        return None

    def _get_breakout_signal(self, df: pd.DataFrame, config: dict) -> tuple | None:
        window = 20
        high_max = df['high'].rolling(window).max().iloc[-2]
        low_min = df['low'].rolling(window).min().iloc[-2]

        atr = AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()
        avg_atr = atr.rolling(50).mean().iloc[-1]

        if df['close'].iloc[-1] > high_max and atr.iloc[-1] > avg_atr:
            return ("buy", 0.9)
        elif df['close'].iloc[-1] < low_min and atr.iloc[-1] > avg_atr:
            return ("sell", 0.9)
        return None

    def generate_signal(self, df: pd.DataFrame, symbol: str, regime: str = None) -> tuple | None:
        """
        Rule-based hybrid signal.
        Returns (side, confidence, strategy_type)
        """
        try:
            if regime is None:
                regime = self.detect_regime(df)

            config = SYMBOLS_CONFIG.get(symbol, SYMBOLS_CONFIG["EURUSD"])
            sentiment_score = self.news_sentiment.get_sentiment(symbol)

            signals = []

            # 1. Momentum
            mom = self._get_momentum_signal(df, config)
            if mom: signals.append((*mom, "momentum"))

            # 2. Mean Reversion
            mr = self._get_mean_reversion_signal(df, config)
            if mr: signals.append((*mr, "mean_reversion"))

            # 3. Pullback
            pb = self._get_pullback_signal(df, config)
            if pb: signals.append((*pb, "pullback"))

            # 4. Breakout
            bo = self._get_breakout_signal(df, config)
            if bo: signals.append((*bo, "breakout"))

            if not signals:
                return None

            # Pick signal with highest confidence
            best_signal = max(signals, key=lambda x: x[1])
            side, confidence, strategy = best_signal

            # Adjust confidence with sentiment
            if side == "buy":
                confidence += (sentiment_score * 0.1)
            else:
                confidence -= (sentiment_score * 0.1)

            return (side, min(1.0, max(0.0, confidence)), strategy)

        except Exception as e:
            logger.error(f"{symbol}: SignalEngine failed | {e}")
            return None
