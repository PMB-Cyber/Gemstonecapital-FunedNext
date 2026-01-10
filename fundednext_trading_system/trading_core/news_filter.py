import time
from datetime import datetime, timedelta
from fundednext_trading_system.config.news_config import (
    NEWS_PAUSE_BEFORE,
    NEWS_PAUSE_AFTER,
    HIGH_IMPACT_THRESHOLD
)

# Stub: replace with cached calendar feed later
_HIGH_IMPACT_EVENTS = []

def update_news_cache(events):
    global _HIGH_IMPACT_EVENTS
    _HIGH_IMPACT_EVENTS = events


def is_news_pause_active() -> bool:
    now = datetime.utcnow()

    for event in _HIGH_IMPACT_EVENTS:
        impact = event.get("impact", 0)
        event_time = event.get("time")

        if impact < HIGH_IMPACT_THRESHOLD:
            continue

        if not isinstance(event_time, datetime):
            continue

        if event_time - timedelta(seconds=NEWS_PAUSE_BEFORE) <= now <= event_time + timedelta(seconds=NEWS_PAUSE_AFTER):
            return True

    return False
