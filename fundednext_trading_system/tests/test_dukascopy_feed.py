import unittest
from unittest.mock import patch, MagicMock
from fundednext_trading_system.execution.dukascopy_data_feed import DukascopyDataFeed
import pandas as pd
from datetime import datetime

class TestDukascopyDataFeed(unittest.TestCase):

    @patch('dukascopy_python.fetch')
    def test_get_candles_success(self, mock_fetch):
        # Create a mock DataFrame to be returned by the fetch function
        mock_df = pd.DataFrame({
            'timestamp': [datetime(2023, 1, 1, 0, 0, 0), datetime(2023, 1, 1, 0, 0, 1)],
            'bidPrice': [1.0, 1.1],
            'askPrice': [1.01, 1.11],
            'bidVolume': [100, 110],
            'askVolume': [101, 111]
        }).set_index('timestamp')
        mock_fetch.return_value = mock_df

        # Initialize the data feed and get candles
        feed = DukascopyDataFeed()
        df = feed.get_candles('EURUSD', 60, 1)

        # Assertions
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 1)
        self.assertIn('time', df.columns)
        self.assertIn('open', df.columns)
        self.assertIn('high', df.columns)
        self.assertIn('low', df.columns)
        self.assertIn('close', df.columns)
        self.assertIn('tick_volume', df.columns)

    @patch('dukascopy_python.fetch')
    def test_get_candles_failure(self, mock_fetch):
        # Mock the fetch function to raise an exception
        mock_fetch.side_effect = Exception("Test Error")

        # Initialize the data feed and get candles
        feed = DukascopyDataFeed()
        df = feed.get_candles('EURUSD', 300, 1)

        # Assertions
        self.assertIsNone(df)

if __name__ == '__main__':
    unittest.main()
