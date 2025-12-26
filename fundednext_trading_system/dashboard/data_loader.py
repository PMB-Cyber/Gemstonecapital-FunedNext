import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime


def get_account_info():
    if not mt5.initialize():
        return None

    info = mt5.account_info()
    if info is None:
        return None

    return {
        "balance": info.balance,
        "equity": info.equity,
        "profit": info.profit,
        "margin": info.margin,
        "free_margin": info.margin_free,
    }


def get_open_positions():
    positions = mt5.positions_get()
    if positions is None:
        return []

    data = []
    for p in positions:
        data.append({
            "symbol": p.symbol,
            "type": "BUY" if p.type == 0 else "SELL",
            "volume": p.volume,
            "profit": p.profit,
            "price_open": p.price_open,
            "price_current": p.price_current,
        })

    return pd.DataFrame(data)


def get_trade_history(days=7):
    from_date = datetime.now().replace(hour=0, minute=0)
    deals = mt5.history_deals_get(from_date, datetime.now())

    if deals is None:
        return pd.DataFrame()

    rows = []
    for d in deals:
        rows.append({
            "time": datetime.fromtimestamp(d.time),
            "symbol": d.symbol,
            "profit": d.profit,
            "volume": d.volume,
        })

    return pd.DataFrame(rows)
