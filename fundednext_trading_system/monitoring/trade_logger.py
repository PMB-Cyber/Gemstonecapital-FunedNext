import csv
from pathlib import Path
from datetime import datetime

TRADE_FILE = Path("data/trades.csv")

if not TRADE_FILE.exists():
    with open(TRADE_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp",
            "symbol",
            "direction",
            "volume",
            "entry_price",
            "sl",
            "tp",
            "result",
            "pnl"
        ])

def log_trade(trade: dict):
    with open(TRADE_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.utcnow().isoformat(),
            trade.get("symbol"),
            trade.get("signal"),
            trade.get("volume"),
            trade.get("price"),
            trade.get("sl"),
            trade.get("tp"),
            trade.get("result"),
            trade.get("pnl"),
        ])
