import csv
import os
from datetime import datetime

LOG_PATH = "logs/shadow_model.csv"
os.makedirs("logs", exist_ok=True)

HEADER = [
    "timestamp",
    "symbol",
    "side",
    "confidence",
    "price",
]

def log_shadow_signal(symbol, side, confidence, price):
    write_header = not os.path.exists(LOG_PATH)

    with open(LOG_PATH, "a", newline="") as f:
        writer = csv.writer(f)

        if write_header:
            writer.writerow(HEADER)

        writer.writerow([
            datetime.utcnow().isoformat(),
            symbol,
            side,
            round(confidence, 4),
            price,
        ])
