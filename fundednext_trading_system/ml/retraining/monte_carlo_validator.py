import numpy as np
import pandas as pd

from fundednext_trading_system.monitoring.logger import logger


class MonteCarloValidator:
    """
    Monte Carlo simulator to validate model robustness.
    Prevents overfitting / luck-based models from deployment.
    """

    def __init__(
        self,
        simulations: int = 5000,
        min_sharpe: float = 0.8,
        max_risk_of_ruin: float = 0.25,
        starting_equity: float = 1.0,
    ):
        self.simulations = simulations
        self.min_sharpe = min_sharpe
        self.max_risk_of_ruin = max_risk_of_ruin
        self.starting_equity = starting_equity

    # =========================
    # PUBLIC ENTRY
    # =========================
    def validate(self, trade_returns: pd.Series) -> bool:
        if trade_returns.empty or len(trade_returns) < 50:
            logger.error("❌ Monte Carlo rejected — insufficient trade history")
            return False

        paths = self._simulate_equity_paths(trade_returns)

        sharpe = self._calculate_sharpe(paths)
        risk_of_ruin = self._calculate_risk_of_ruin(paths)

        logger.info(
            f"📊 Monte Carlo results | Sharpe={sharpe:.2f} | RoR={risk_of_ruin:.2%}"
        )

        if sharpe < self.min_sharpe:
            logger.critical("❌ Monte Carlo FAIL — Sharpe too low")
            return False

        if risk_of_ruin > self.max_risk_of_ruin:
            logger.critical("❌ Monte Carlo FAIL — Risk of Ruin too high")
            return False

        logger.success("✅ Monte Carlo validation PASSED")
        return True

    # =========================
    # CORE SIMULATION
    # =========================
    def _simulate_equity_paths(self, returns: pd.Series) -> np.ndarray:
        returns = returns.values
        n = len(returns)

        paths = np.zeros((self.simulations, n))
        for i in range(self.simulations):
            sampled = np.random.choice(returns, size=n, replace=True)
            paths[i] = np.cumprod(1 + sampled)

        return paths

    # =========================
    # METRICS
    # =========================
    def _calculate_sharpe(self, paths: np.ndarray) -> float:
        final_returns = paths[:, -1] - 1.0
        mean = np.mean(final_returns)
        std = np.std(final_returns)

        if std == 0:
            return 0.0

        return mean / std

    def _calculate_risk_of_ruin(
        self,
        paths: np.ndarray,
        ruin_level: float = 0.7,
    ) -> float:
        ruined = np.any(paths < ruin_level, axis=1)
        return np.mean(ruined)
