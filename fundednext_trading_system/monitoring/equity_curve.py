equity_curve = []

def update_equity(current_equity):
    equity_curve.append(current_equity)

def max_drawdown():
    peak = equity_curve[0]
    max_dd = 0.0

    for equity in equity_curve:
        peak = max(peak, equity)
        dd = (peak - equity)
        max_dd = max(max_dd, dd)

    return max_dd
