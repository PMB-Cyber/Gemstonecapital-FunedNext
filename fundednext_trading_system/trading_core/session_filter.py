from datetime import datetime
from fundednext_trading_system.config.sessions import LONDON_SESSION, NEW_YORK_SESSION, FRIDAY_CLOSE_HOUR

def _utc_now():
    return datetime.utcnow()

def is_weekend() -> bool:
    return _utc_now().weekday() >= 5

def is_friday_close_window() -> bool:
    now = _utc_now()
    return now.weekday() == 4 and now.hour >= FRIDAY_CLOSE_HOUR

def is_within_trading_session() -> bool:
    now = _utc_now()

    if is_weekend():
        return False

    if is_friday_close_window():
        return False

    hour = now.hour
    in_london = LONDON_SESSION[0] <= hour < LONDON_SESSION[1]
    in_ny = NEW_YORK_SESSION[0] <= hour < NEW_YORK_SESSION[1]

    return in_london or in_ny
