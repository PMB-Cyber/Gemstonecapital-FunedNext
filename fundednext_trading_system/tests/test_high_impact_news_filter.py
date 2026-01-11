import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import pytz

# Mock the MetaTrader5 library before importing the class that uses it
import sys
sys.modules['MetaTrader5'] = MagicMock()

from fundednext_trading_system.trading_core.high_impact_news_filter import HighImpactNewsFilter

# Create a mock news item class that mimics the structure returned by mt5.news_get()
class MockNewsItem:
    def __init__(self, dt, subject):
        self.datetime = dt.timestamp()
        self.subject = subject

class TestHighImpactNewsFilter(unittest.TestCase):

    @patch('MetaTrader5.news_get')
    def test_is_trade_locked_no_news(self, mock_news_get):
        mock_news_get.return_value = []
        news_filter = HighImpactNewsFilter(lock_minutes=30)
        self.assertFalse(news_filter.is_trade_locked("EURUSD"))

    @patch('MetaTrader5.news_get')
    def test_is_trade_locked_with_non_high_impact_news(self, mock_news_get):
        now = datetime.now(pytz.utc)
        # The filter only looks for "HIGH" in the subject
        news_item = MockNewsItem(now, "USD Non-Farm Payrolls")
        mock_news_get.return_value = [news_item]
        news_filter = HighImpactNewsFilter(lock_minutes=30)
        # Since no "HIGH" is in the subject, no event should be stored
        self.assertFalse(news_filter.is_trade_locked("EURUSD"))

    @patch('MetaTrader5.news_get')
    def test_is_trade_locked_with_high_impact_news(self, mock_news_get):
        now = datetime.now(pytz.utc)
        news_item = MockNewsItem(now, "USD HIGH Non-Farm Payrolls")
        mock_news_get.return_value = [news_item]
        news_filter = HighImpactNewsFilter(lock_minutes=30)
        # The trade should be locked because the current time is within the lock window
        self.assertTrue(news_filter.is_trade_locked("EURUSD"))

    @patch('MetaTrader5.news_get')
    def test_is_trade_locked_outside_lock_duration(self, mock_news_get):
        # Event happened 31 minutes ago, outside the 30-minute lock window
        event_time = datetime.now(pytz.utc) - timedelta(minutes=31)
        news_item = MockNewsItem(event_time, "USD HIGH Non-Farm Payrolls")
        mock_news_get.return_value = [news_item]
        news_filter = HighImpactNewsFilter(lock_minutes=30)
        self.assertFalse(news_filter.is_trade_locked("EURUSD"))

    @patch('MetaTrader5.news_get')
    def test_is_trade_locked_inside_lock_duration_before_event(self, mock_news_get):
        # Event is in 29 minutes, inside the 30-minute lock window
        event_time = datetime.now(pytz.utc) + timedelta(minutes=29)
        news_item = MockNewsItem(event_time, "USD HIGH Non-Farm Payrolls")
        mock_news_get.return_value = [news_item]
        news_filter = HighImpactNewsFilter(lock_minutes=30)
        self.assertTrue(news_filter.is_trade_locked("EURUSD"))

    @patch('MetaTrader5.news_get')
    def test_is_trade_locked_inside_lock_duration_after_event(self, mock_news_get):
        # Event was 29 minutes ago, inside the 30-minute lock window
        event_time = datetime.now(pytz.utc) - timedelta(minutes=29)
        news_item = MockNewsItem(event_time, "USD HIGH Non-Farm Payrolls")
        mock_news_get.return_value = [news_item]
        news_filter = HighImpactNewsFilter(lock_minutes=30)
        self.assertTrue(news_filter.is_trade_locked("EURUSD"))

    @patch('MetaTrader5.news_get')
    def test_is_trade_locked_different_currency(self, mock_news_get):
        now = datetime.now(pytz.utc)
        news_item = MockNewsItem(now, "JPY HIGH BOJ Policy Rate")
        mock_news_get.return_value = [news_item]
        news_filter = HighImpactNewsFilter(lock_minutes=30)
        # The symbol EURUSD does not contain JPY, so it should not be locked
        self.assertFalse(news_filter.is_trade_locked("EURUSD"))
        # The symbol USDJPY does contain JPY, so it should be locked
        self.assertTrue(news_filter.is_trade_locked("USDJPY"))


if __name__ == '__main__':
    unittest.main()
