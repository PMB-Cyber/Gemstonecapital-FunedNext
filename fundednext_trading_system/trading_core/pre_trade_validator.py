from fundednext_trading_system.offline_training.offline_training import MonteCarloValidator
from fundednext_trading_system.monitoring.logger import logger

class PreTradeValidator:
    def __init__(self):
        self.validator = MonteCarloValidator(simulations=100)  # Faster validation

    def validate_trade(self, df, signal, model, features):
        """
        Runs an on-the-fly Monte Carlo validation for a single trade signal.
        """
        trade_returns = self._run_simplified_backtest(df, model, features)
        if not trade_returns:
            logger.warning("Could not generate trade returns for pre-trade validation.")
            return False

        report = self.validator.run(trade_returns)
        if not report["passed"]:
            logger.warning(f"Pre-trade validation failed: {report}")
            return False

        logger.success("Pre-trade validation passed.")
        return True

    def _run_simplified_backtest(self, df, model, features, backtest_bars=100):
        """
        Runs a simplified backtest on the most recent data.
        """
        trade_returns = []
        recent_df = df.tail(backtest_bars)
        recent_features = features.tail(backtest_bars)

        for i in range(1, len(recent_features)):
            if i >= len(recent_df) - 1:
                break

            current_features = recent_features.iloc[i:i+1]

            try:
                pred_proba = model.predict_proba(current_features.values)
                side = "buy" if pred_proba[0][1] > pred_proba[0][0] else "sell"

                price_change = recent_df['close'].iloc[i+1] - recent_df['close'].iloc[i]

                if side == "buy":
                    trade_returns.append(price_change / recent_df['close'].iloc[i])
                else: # sell
                    trade_returns.append(-price_change / recent_df['close'].iloc[i])
            except Exception as e:
                logger.warning(f"Could not make prediction at step {i}: {e}")
                continue

        return trade_returns
