import os

TRADE_ENABLED = os.getenv("TRADE_ENABLED", "false").lower() == "true"
