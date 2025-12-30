import unittest
from unittest.mock import patch, MagicMock
from fundednext_trading_system.trading_core.risk_manager import RiskManager

class MockPosition:
    def __init__(self, symbol):
        self.symbol = symbol

@patch('fundednext_trading_system.trading_core.risk_manager.CorrelationManager')
class TestRiskManager(unittest.TestCase):

    def test_can_open_trade_with_correlation_check(self, MockCorrelationManager):
        # Configure the mock CorrelationManager instance
        mock_corr_manager_instance = MockCorrelationManager.return_value
        mock_corr_manager_instance.matrix_ready = True

        # Initialize the risk manager (it will receive the mocked CorrelationManager)
        risk_manager = RiskManager()

        # Test case 1: No open positions, should be allowed
        self.assertTrue(risk_manager.can_open_trade(risk_amount=100, symbol='EURUSD', open_positions=[]))

        # Test case 2: High correlation with an open position, should be blocked
        open_positions = [MockPosition('GBPUSD')]
        mock_corr_manager_instance.get_correlation.return_value = 0.9 # High correlation
        self.assertFalse(risk_manager.can_open_trade(risk_amount=100, symbol='EURUSD', open_positions=open_positions))
        # Verify get_correlation was called correctly
        mock_corr_manager_instance.get_correlation.assert_called_with('EURUSD', 'GBPUSD')

        # Test case 3: Low correlation with an open position, should be allowed
        mock_corr_manager_instance.get_correlation.return_value = 0.5 # Low correlation
        self.assertTrue(risk_manager.can_open_trade(risk_amount=100, symbol='EURUSD', open_positions=open_positions))
        mock_corr_manager_instance.get_correlation.assert_called_with('EURUSD', 'GBPUSD')


if __name__ == '__main__':
    unittest.main()
