from config.allowed_symbols import ALLOWED_SYMBOLS
from trading_core.session_filter import is_within_trading_session
from trading_core.flat_guard import must_force_flat

def validate_order(symbol: str) -> bool:
    if symbol not in ALLOWED_SYMBOLS:
        return False
    if not is_within_trading_session():
        return False
    if must_force_flat():
        return False
    return True
