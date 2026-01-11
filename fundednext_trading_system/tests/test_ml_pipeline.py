import unittest
from unittest.mock import MagicMock, patch
from fundednext_trading_system.trading_core.pre_trade_validator import PreTradeValidator
from fundednext_trading_system.ml.retraining.retraining_manager import RetrainingManager
import pandas as pd
from datetime import datetime

class TestMLPipeline(unittest.TestCase):

    def test_pre_trade_validator(self):
        # Mock the MonteCarloValidator
        validator = PreTradeValidator()
        validator.validator = MagicMock()
        validator.validator.run.return_value = {"passed": True}

        # Create a mock DataFrame that can be sliced
        df = pd.DataFrame({'close': [1.0, 1.1, 1.2, 1.3, 1.4]})

        # Create a mock features object that can be sliced
        features = pd.DataFrame({'feature1': [0.1, 0.2, 0.3, 0.4, 0.5]})

        signal = ("buy", 0.8)
        model = MagicMock()
        model.predict_proba.return_value = [[0.2, 0.8]]

        # Validate the trade
        result = validator.validate_trade(df, signal, model, features)

        # Assertions
        self.assertTrue(result)

    @patch('subprocess.Popen')
    def test_retraining_manager(self, mock_popen):
        # Create a RetrainingManager
        retraining_manager = RetrainingManager()

        # Trigger retraining
        retraining_manager.trigger_retraining("EURUSD")

        # Assertions
        mock_popen.assert_called_once()

if __name__ == '__main__':
    unittest.main()
