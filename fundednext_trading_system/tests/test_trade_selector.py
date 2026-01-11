import unittest
from unittest.mock import MagicMock
from fundednext_trading_system.trading_core.trade_selector import TradeSelector

class TestTradeSelector(unittest.TestCase):

    def test_select_best_trades(self):
        # Mock the CorrelationManager
        correlation_manager = MagicMock()
        correlation_manager.matrix_ready = True
        correlation_manager.get_correlation.side_effect = lambda s1, s2: 0.9 if (s1, s2) in [('EURUSD', 'GBPUSD'), ('GBPUSD', 'EURUSD')] else 0.1

        # Create a TradeSelector with the mocked CorrelationManager
        trade_selector = TradeSelector(correlation_manager)

        # Create some potential trades
        potential_trades = [
            {'symbol': 'EURUSD', 'score': 0.8},
            {'symbol': 'GBPUSD', 'score': 0.9},
            {'symbol': 'USDJPY', 'score': 0.7},
        ]

        # Select the best trades
        selected_trades = trade_selector.select_best_trades(potential_trades)

        # Assertions
        self.assertEqual(len(selected_trades), 2)
        self.assertEqual(selected_trades[0]['symbol'], 'GBPUSD')
        self.assertEqual(selected_trades[1]['symbol'], 'USDJPY')

if __name__ == '__main__':
    unittest.main()
