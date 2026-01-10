from fundednext_trading_system.trading_core.session_filter import is_weekend, is_friday_close_window

def must_force_flat() -> bool:
    return is_weekend() or is_friday_close_window()
