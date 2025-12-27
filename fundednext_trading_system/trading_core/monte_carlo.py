import numpy as np

def monte_carlo_simulate(returns, runs=10000):
    equity_curves = []

    for _ in range(runs):
        sampled = np.random.choice(returns, size=len(returns), replace=True)
        equity_curves.append(np.cumsum(sampled))

    return {
        "worst_dd": min(min(ec) for ec in equity_curves),
        "best_run": max(max(ec) for ec in equity_curves),
        "risk_of_ruin": sum(min(ec) < -0.04 for ec in equity_curves) / runs,
    }
