import numpy as np
import json
from fundednext_trading_system.monitoring.logger import logger

class MonteCarloValidator:
    def __init__(
        self,
        min_win_rate=0.52,
        max_drawdown=0.08,
        simulations=1000,
    ):
        self.min_win_rate = min_win_rate
        self.max_drawdown = max_drawdown
        self.simulations = simulations

    def run(self, trade_returns):
        """
        trade_returns: list of % returns per trade (e.g. +0.01, -0.005)
        """
        results = []
        trade_count = len(trade_returns)

        for _ in range(self.simulations):
            np.random.shuffle(trade_returns) # Shuffle in place

            equity = 1.0
            peak = 1.0
            max_dd = 0.0
            wins = 0

            for r in trade_returns:
                equity *= (1 + r)
                peak = max(peak, equity)
                drawdown = (peak - equity) / peak
                max_dd = max(max_dd, drawdown)
                if r > 0:
                    wins += 1

            results.append({
                "final_equity": equity,
                "max_dd": max_dd,
                "win_rate": wins / trade_count,
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
