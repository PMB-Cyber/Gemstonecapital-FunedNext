import numpy as np


def sharpe_ratio(returns, risk_free=0.0):
    if len(returns) < 2:
        return 0.0
    excess = returns - risk_free
    return np.mean(excess) / (np.std(excess) + 1e-9)


def max_drawdown(equity_curve):
    peak = equity_curve[0]
    max_dd = 0

    for value in equity_curve:
        peak = max(peak, value)
        dd = (peak - value)
        max_dd = max(max_dd, dd)

    return max_dd
