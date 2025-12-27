# Mock MetaTrader5 module
import pandas as pd
import numpy as np

def initialize():
    return True

def shutdown():
    pass

class AccountInfo:
    def __init__(self, login, equity, margin_free, balance):
        self.login = login
        self.equity = equity
        self.margin_free = margin_free
        self.balance = balance

def account_info():
    return AccountInfo(
        login='12345',
        equity=100000.0,
        margin_free=100000.0,
        balance=100000.0
    )

class Tick:
    def __init__(self, ask, bid):
        self.ask = ask
        self.bid = bid

def symbol_info_tick(symbol):
    return Tick(
        ask=1.12345,
        bid=1.12340
    )

class SymbolInfo:
    def __init__(self, point, visible, trade_mode):
        self.point = point
        self.visible = visible
        self.trade_mode = trade_mode

TIMEFRAME_M1 = 1
SYMBOL_TRADE_MODE_FULL = 0

def symbol_info(symbol):
    return SymbolInfo(
        point=0.00001,
        visible=True,
        trade_mode=SYMBOL_TRADE_MODE_FULL
    )

def positions_get(symbol=None):
    return []

def copy_rates_from_pos(symbol, timeframe, start_pos, count):
    # Return a DataFrame with the correct columns
    return pd.DataFrame({
        'time': pd.to_datetime(np.arange(count), unit='s'),
        'open': np.random.rand(count) * 100,
        'high': np.random.rand(count) * 100,
        'low': np.random.rand(count) * 100,
        'close': np.random.rand(count) * 100,
        'tick_volume': np.random.randint(100, 1000, count),
        'spread': np.random.randint(0, 10, count),
        'real_volume': np.random.randint(1000, 10000, count)
    })

print("USING MOCK METATRADER5 MODULE")
