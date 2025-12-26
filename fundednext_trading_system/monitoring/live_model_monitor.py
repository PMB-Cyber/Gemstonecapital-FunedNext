from trading_core.model_rollback import ModelRollbackGuard
from monitoring.logger import logger


class LiveModelMonitor:
    def __init__(self):
        self.guard = ModelRollbackGuard()

    def evaluate(self, symbol: str, stats: dict):
        """
        stats must include:
        sharpe, risk_of_ruin, consecutive_losses, drawdown
        """
        if self.guard.evaluate(stats):
            self.guard.rollback(symbol)
            logger.critical(
                f"🚨 LIVE MODEL ROLLBACK EXECUTED for {symbol}"
            )
            return False

        return True
