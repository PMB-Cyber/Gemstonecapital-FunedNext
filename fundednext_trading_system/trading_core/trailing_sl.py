import numpy as np
from monitoring.logger import logger

def calculate_atr(df, period=14):
    high_low = df["high"] - df["low"]
    high_close = np.abs(df["high"] - df["close"].shift())
    low_close = np.abs(df["low"] - df["close"].shift())
    tr = np.maximum.reduce([high_low, high_close, low_close])
    return tr.rolling(period).mean().iloc[-1]


def should_trail(position, current_price, atr, direction):
    if direction == "buy":
        return current_price > position.price_open + atr
    else:
        return current_price < position.price_open - atr


def new_trailing_sl(position, atr, direction):
    if direction == "buy":
        return position.price_current - atr
    else:
        return position.price_current + atr
