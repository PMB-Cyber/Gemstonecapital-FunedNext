import unittest
from unittest.mock import patch, MagicMock
from fundednext_trading_system.execution.dukascopy_data_feed import DukascopyDataFeed
import pandas as pd
from datetime import datetime

class TestDukascopyDataFeed(unittest.TestCase):

    def setUp(self):
        # Create a standard mock DataFrame to be reused in tests
        self.mock_df = pd.DataFrame({
            'timestamp': pd.to_datetime(['2023-01-01 00:00:00', '2023-01-01 00:00:01']),
            'bidPrice': [1.0, 1.1],
            'askPrice': [1.01, 1.11],
            'bidVolume': [100, 110],
            'askVolume': [101, 111]
        }).set_index('timestamp')

    @patch('dukascopy_python.fetch')
    def test_get_candles_success(self, mock_fetch):
        mock_fetch.return_value = self.mock_df

        feed = DukascopyDataFeed()
        df = feed.get_candles('EURUSD', 60, 1)

        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 1)
        self.assertIn('time', df.columns)
        self.assertIn('open', df.columns)
        self.assertIn('high', df.columns)
        self.assertIn('low', df.columns)
        self.assertIn('close', df.columns)
        self.assertIn('tick_volume', df.columns)

    @patch('dukascopy_python.fetch')
    def test_get_candles_api_exception_triggers_retry(self, mock_fetch):
        # Simulate an API exception on the first call, then success
        mock_fetch.side_effect = [Exception("API Error"), self.mock_df]

        feed = DukascopyDataFeed()
        df = feed.get_candles('EURUSD', 300, 1, max_retries=2)

        # Assert that fetch was called twice (1 initial + 1 retry)
        self.assertEqual(mock_fetch.call_count, 2)
        # Assert that we received the DataFrame on the second attempt
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 1)

    @patch('dukascopy_python.fetch')
    def test_get_candles_empty_dataframe_triggers_retry(self, mock_fetch):
        # Simulate an empty DataFrame on the first call, then success
        mock_fetch.side_effect = [pd.DataFrame(), self.mock_df]

        feed = DukascopyDataFeed()
        df = feed.get_candles('EURUSD', 300, 1, max_retries=2)

        self.assertEqual(mock_fetch.call_count, 2)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 1)

    @patch('dukascopy_python.fetch')
    def test_get_candles_failure_after_max_retries(self, mock_fetch):
        # Simulate persistent failure
        mock_fetch.side_effect = Exception("Persistent API Error")

        feed = DukascopyDataFeed()
        df = feed.get_candles('EURUSD', 300, 1, max_retries=3)

        # Should be called 3 times (1 initial + 2 retries)
        self.assertEqual(mock_fetch.call_count, 3)
        # Should return None after all retries fail
        self.assertIsNone(df)

    @patch('dukascopy_python.fetch')
    def test_correct_symbol_mapping_for_us30(self, mock_fetch):
        mock_fetch.return_value = self.mock_df

        feed = DukascopyDataFeed()
        feed.get_candles('US30', 60, 1)

        # Verify that the symbol passed to the fetch function was 'usa30'
        called_symbol = mock_fetch.call_args[0][0]
        self.assertEqual(called_symbol, 'usa30')

    def test_unsupported_symbol(self):
        feed = DukascopyDataFeed()
        df = feed.get_candles('UNSUPPORTED', 60, 1)
        self.assertIsNone(df)

if __name__ == '__main__':
    unittest.main()
