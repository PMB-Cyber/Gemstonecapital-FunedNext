# execution/symbol_stats_manager.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class SymbolStatsManager:
    """
    Tracks per-symbol stats: trades, wins/losses, PnL, regime detection, and cooldown.
    Regimes: 'trend' vs 'range'.
    """

    def __init__(self, cooldown_seconds: int = 60):
        self.stats = {}
        self.window = 50  # bars for regime detection
        self.cooldown = timedelta(seconds=cooldown_seconds)

    def init_symbol(self, symbol: str):
        if symbol not in self.stats:
            self.stats[symbol] = {
                "trades": 0,
                "wins": 0,
                "losses": 0,
                "pnl": 0.0,
                "regime": "unknown",
                "last_trade": None,
            }

    def register_trade(self, symbol: str, profit: float):
        self.init_symbol(symbol)
        self.stats[symbol]["trades"] += 1
        self.stats[symbol]["pnl"] += profit
        if profit > 0:
            self.stats[symbol]["wins"] += 1
        else:
            self.stats[symbol]["losses"] += 1
        self.stats[symbol]["last_trade"] = datetime.utcnow()

    def detect_regime(self, symbol: str, df: pd.DataFrame) -> str:
        """
        Detects 'trend' or 'range' based on recent ATR vs price movement.
        """
        self.init_symbol(symbol)
        if len(df) < self.window:
            return "unknown"

        recent = df[-self.window:]
        high = recent['high']
        low = recent['low']
        close = recent['close']

        tr = np.maximum(high - low, np.maximum(abs(high - close.shift(1)), abs(low - close.shift(1))))
        atr = tr.rolling(window=14).mean().iloc[-1]

        price_range = high.iloc[-1] - low.iloc[-1]
        regime = "trend" if price_range > 2 * atr else "range"

        self.stats[symbol]["regime"] = regime
        return regime

    def can_trade(self, symbol: str) -> bool:
        """
        Enforces cooldown per symbol.
        """
        self.init_symbol(symbol)
        last = self.stats[symbol]["last_trade"]
        if last is None:
            return True
        return datetime.utcnow() - last >= self.cooldown

    def get_stats(self, symbol: str):
        self.init_symbol(symbol)
        return self.stats[symbol]
