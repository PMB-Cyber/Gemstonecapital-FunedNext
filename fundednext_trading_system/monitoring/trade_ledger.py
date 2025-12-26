from dataclasses import dataclass
from datetime import datetime

@dataclass
class TradeRecord:
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    volume: float
    pnl: float
    model_version: str
    timestamp: datetime
