import json
import os
from fundednext_trading_system.monitoring.logger import logger
from fundednext_trading_system.trading_core.model_guard import promote_model_version

STATE_FILE = "models/active/model_state.json"


class ModelRollbackGuard:
    def __init__(
        self,
        min_sharpe=0.4,
        max_risk_of_ruin=0.35,
        max_consecutive_losses=6,
        max_drawdown=0.06,
    ):
        self.min_sharpe = min_sharpe
        self.max_risk_of_ruin = max_risk_of_ruin
        self.max_consecutive_losses = max_consecutive_losses
        self.max_drawdown = max_drawdown

    def evaluate(self, stats: dict) -> bool:
        """
        Returns True if rollback is required
        """
        if stats["sharpe"] < self.min_sharpe:
            logger.critical("⚠️ Rollback triggered — Sharpe breach")
            return True

        if stats["risk_of_ruin"] > self.max_risk_of_ruin:
            logger.critical("⚠️ Rollback triggered — RoR breach")
            return True

        if stats["consecutive_losses"] >= self.max_consecutive_losses:
            logger.critical("⚠️ Rollback triggered — Loss streak")
            return True

        if stats["drawdown"] >= self.max_drawdown:
            logger.critical("⚠️ Rollback triggered — Drawdown breach")
            return True

        return False

    def rollback(self, symbol: str):
        logger.critical(f"🔁 Rolling back model for {symbol}")

        if not os.path.exists(STATE_FILE):
            raise RuntimeError("No model state file found")

        with open(STATE_FILE, "r") as f:
            state = json.load(f)

        previous_model = state.get(symbol, {}).get("previous")

        if not previous_model:
            raise RuntimeError("No previous model available")

        promote_model_version(symbol, previous_model)

        logger.success(
            f"✅ Model rollback complete for {symbol} → {previous_model}"
        )
