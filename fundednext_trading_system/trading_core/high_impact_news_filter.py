import MetaTrader5 as mt5
from datetime import datetime, timedelta
from fundednext_trading_system.monitoring.logger import logger

class HighImpactNewsFilter:
    def __init__(self, lock_minutes=30):
        self.lock_period = timedelta(minutes=lock_minutes)
        self.high_impact_events = []
        self._fetch_news()

    def _fetch_news(self):
        """
        Fetches news from the MT5 platform and identifies high-impact events.
        """
        try:
            news = mt5.news_get()
            if news:
                for item in news:
                    if "HIGH" in item.subject:
                        self.high_impact_events.append({
                            "time": datetime.fromtimestamp(item.datetime),
                            "subject": item.subject,
                            "currency": self._extract_currency(item.subject)
                        })
                logger.info(f"Fetched {len(self.high_impact_events)} high-impact news events.")
        except Exception as e:
            logger.error(f"Error fetching news from MT5: {e}")

    def _extract_currency(self, subject):
        """
        Extracts the currency from the news subject.
        """
        # This is a simplified implementation. A more robust implementation
        # would use a more sophisticated method to extract the currency.
        parts = subject.split()
        if len(parts) > 1:
            return parts[0]
        return None

    def is_trade_locked(self, symbol):
        """
        Checks if trading is locked for a given symbol due to a high-impact news event.
        """
        now = datetime.utcnow()
        for event in self.high_impact_events:
            if event["currency"] and event["currency"] in symbol:
                if now >= event["time"] - self.lock_period and now <= event["time"] + self.lock_period:
                    logger.warning(f"Trade for {symbol} locked due to high-impact news event: {event['subject']}")
                    return True
        return False
