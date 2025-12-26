import os

TRADING_MODE = os.getenv("TRADING_MODE", "CHALLENGE").upper()

if TRADING_MODE not in ("CHALLENGE", "FUNDED"):
    raise RuntimeError(f"Invalid TRADING_MODE: {TRADING_MODE}")
