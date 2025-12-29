import numpy as np
import json
from fundednext_trading_system.monitoring.logger import logger

class MonteCarloValidator:
    def __init__(
        self,
        min_win_rate=0.52,
        max_drawdown=0.08,
        simulations=1000,
        trade_count=200,
    ):
        self.min_win_rate = min_win_rate
        self.max_drawdown = max_drawdown
        self.simulations = simulations
        self.trade_count = trade_count

    def run(self, trade_returns):
        """
        trade_returns: list of % returns per trade (e.g. +0.01, -0.005)
        """
        results = []

        for _ in range(self.simulations):
            sample = np.random.choice(
                trade_returns,
                size=self.trade_count,
                replace=True,
            )

            equity = 1.0
            peak = 1.0
            max_dd = 0.0
            wins = 0

            for r in sample:
                equity *= (1 + r)
                peak = max(peak, equity)
                drawdown = (peak - equity) / peak
                max_dd = max(max_dd, drawdown)
                if r > 0:
                    wins += 1

            results.append({
                "final_equity": equity,
                "max_dd": max_dd,
                "win_rate": wins / self.trade_count,
            })

        return self._evaluate(results)

    def _evaluate(self, results):
        avg_win_rate = np.mean([r["win_rate"] for r in results])
        worst_dd = np.max([r["max_dd"] for r in results])
        median_equity = np.median([r["final_equity"] for r in results])

        passed = (
            avg_win_rate >= self.min_win_rate
            and worst_dd <= self.max_drawdown
        )

        report = {
            "passed": passed,
            "avg_win_rate": round(avg_win_rate, 3),
            "worst_drawdown": round(worst_dd, 3),
            "median_equity": round(median_equity, 3),
            "simulations": self.simulations,
        }

        return report
