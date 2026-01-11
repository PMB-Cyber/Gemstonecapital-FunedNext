import unittest
from unittest.mock import patch, MagicMock
from fundednext_trading_system.trading_core.risk_manager import RiskManager

class MockPosition:
    def __init__(self, symbol):
        self.symbol = symbol

class TestRiskManager(unittest.TestCase):

    def test_can_open_trade(self):
        # Initialize the risk manager
        risk_manager = RiskManager()

        # Test case 1: Should be allowed
        self.assertTrue(risk_manager.can_open_trade(risk_amount=100, symbol='EURUSD'))

if __name__ == '__main__':
    unittest.main()
