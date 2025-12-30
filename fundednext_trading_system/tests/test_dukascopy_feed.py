import unittest
from unittest.mock import patch, MagicMock
from fundednext_trading_system.execution.dukascopy_data_feed import DukascopyDataFeed
import pandas as pd

class TestDukascopyDataFeed(unittest.TestCase):

    @patch('subprocess.Popen')
    def test_get_candles_success(self, mock_popen):
        # Mock the subprocess call
        process_mock = MagicMock()
        process_mock.communicate.return_value = (b'timestamp,open,high,low,close,volume\n1672531200,1.0,1.1,0.9,1.05,100\n', b'')
        process_mock.returncode = 0
        mock_popen.return_value = process_mock

        # Initialize the data feed and get candles
        feed = DukascopyDataFeed()
        df = feed.get_candles('EURUSD', 300, 1)

        # Assertions
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 1)
        self.assertIn('time', df.columns)
        self.assertIn('tick_volume', df.columns)

    @patch('subprocess.Popen')
    def test_get_candles_failure(self, mock_popen):
        # Mock the subprocess call to simulate an error
        process_mock = MagicMock()
        process_mock.communicate.return_value = (b'', b'Error')
        process_mock.returncode = 1
        mock_popen.return_value = process_mock

        # Initialize the data feed and get candles
        feed = DukascopyDataFeed()
        df = feed.get_candles('EURUSD', 300, 1)

        # Assertions
        self.assertIsNone(df)

if __name__ == '__main__':
    unittest.main()
