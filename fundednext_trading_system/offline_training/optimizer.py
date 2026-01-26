"""
optimizer.py

Automated parameter optimization for SignalEngine.
Uses grid search to find the best indicator settings per symbol.
"""

import pandas as pd
import numpy as np
import itertools
from fundednext_trading_system.monitoring.logger import logger
from fundednext_trading_system.trading_core.signal_engine import SignalEngine

class Optimizer:
    def __init__(self, df: pd.DataFrame, symbol: str):
        self.df = df
        self.symbol = symbol
        self.engine = SignalEngine()

    def evaluate_params(self, params: dict) -> float:
        """
        Evaluate a set of parameters using a simple backtest on historical data.
        Returns the total return.
        """
        ema_fast = params['ema_fast']
        ema_slow = params['ema_slow']
        rsi_period = params['rsi_period']

        # We need a custom config for the engine for this evaluation
        custom_config = {
            "ema_fast": ema_fast,
            "ema_slow": ema_slow,
            "rsi_period": rsi_period,
            "atr_period": 14, # default
            "volatility_filter_threshold": 1.5 # default
        }

        total_return = 0.0
        # To speed up, we don't use the full generate_signal loop,
        # but just a simplified version or a subset of the data
        # For simplicity, we'll iterate through every 5th candle
        for i in range(100, len(self.df) - 1, 5):
            window_df = self.df.iloc[:i+1]
            # Override signal engine's config usage for this call
            # This is a bit hacky, so we might want a better way in SignalEngine
            # But for the optimizer, we'll manually check the strategies.

            # For optimization, let's focus on Momentum + Pullback
            mom = self.engine._get_momentum_signal(window_df, custom_config)
            pb = self.engine._get_pullback_signal(window_df, custom_config)

            signal = mom or pb
            if signal:
                side, score = signal
                price_change = self.df['close'].iloc[i+1] - self.df['close'].iloc[i]
                ret = price_change / self.df['close'].iloc[i]
                if side == "buy":
                    total_return += ret
                else:
                    total_return -= ret

        return total_return

    def find_best_params(self) -> dict:
        """
        Runs grid search and returns the best parameters.
        """
        search_space = {
            "ema_fast": [10, 20, 30],
            "ema_slow": [50, 100, 200],
            "rsi_period": [7, 14, 21]
        }

        keys, values = zip(*search_space.items())
        combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]

        best_score = -np.inf
        best_params = None

        logger.info(f"Optimizing parameters for {self.symbol} ({len(combinations)} combinations)...")

        for params in combinations:
            score = self.evaluate_params(params)
            if score > best_score:
                best_score = score
                best_params = params

        logger.success(f"Best params for {self.symbol}: {best_params} (Score: {best_score:.4f})")
        return best_params

def update_symbols_config(symbol: str, best_params: dict):
    """
    Utility to update the symbols_config.py file with new parameters.
    """
    config_path = "fundednext_trading_system/config/symbols_config.py"
    try:
        import sys
        # We need to read the whole file, update the dictionary, and write back.
        # Since it's a python file, we can import it, update the dict, and re-serialize.
        # But to keep formatting, regex might be safer or just overwriting the whole dict.

        from fundednext_trading_system.config.symbols_config import SYMBOLS_CONFIG

        SYMBOLS_CONFIG[symbol].update(best_params)

        with open(config_path, "w") as f:
            f.write("SYMBOLS_CONFIG = {\n")
            for sym, cfg in SYMBOLS_CONFIG.items():
                f.write(f"    \"{sym}\": {cfg},\n")
            f.write("}\n")

        logger.success(f"Updated {config_path} for {symbol}")
    except Exception as e:
        logger.error(f"Failed to update symbols_config: {e}")
