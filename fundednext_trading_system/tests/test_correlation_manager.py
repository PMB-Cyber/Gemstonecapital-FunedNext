import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from fundednext_trading_system.trading_core.correlation_manager import CorrelationManager

class TestCorrelationManager(unittest.TestCase):

    @patch('fundednext_trading_system.trading_core.correlation_manager.threading.Thread')
    @patch('fundednext_trading_system.execution.dukascopy_data_feed.DukascopyDataFeed.get_candles')
    def test_correlation_matrix_calculation(self, mock_get_candles, mock_thread):
        # Mock the Thread class to prevent the background thread from starting
        mock_thread.return_value = MagicMock()

        # Mock the data feed to return sample price data with some noise
        time_index = pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05'])
        mock_data = {
            'EURUSD': pd.DataFrame({'time': time_index, 'close': [1.0, 1.1, 1.2, 1.15, 1.25]}).set_index('time'),
            'GBPUSD': pd.DataFrame({'time': time_index, 'close': [1.2, 1.3, 1.4, 1.35, 1.45]}).set_index('time'),
            'USDJPY': pd.DataFrame({'time': time_index, 'close': [130.0, 129.0, 128.0, 128.5, 127.5]}).set_index('time')
        }

        def side_effect(symbol, timeframe, count):
            df = mock_data.get(symbol)
            if df is not None:
                return df.reset_index()
            return pd.DataFrame()

        mock_get_candles.side_effect = side_effect

        # Initialize the correlation manager
        with patch('fundednext_trading_system.config.settings.ALLOWED_SYMBOLS', ['EURUSD', 'GBPUSD', 'USDJPY']):
            manager = CorrelationManager(days_back=5)
            # Manually call the private method to simulate the thread's execution
            manager._calculate_correlation_matrix(days_back=5)

        # Assertions
        self.assertTrue(manager.matrix_ready)
        self.assertIsNotNone(manager.correlation_matrix)
        self.assertTrue(manager.get_correlation('EURUSD', 'GBPUSD') > 0.9)
        self.assertTrue(manager.get_correlation('EURUSD', 'USDJPY') < -0.9)

if __name__ == '__main__':
    unittest.main()
