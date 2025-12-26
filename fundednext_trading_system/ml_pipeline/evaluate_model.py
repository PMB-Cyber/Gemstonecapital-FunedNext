from monte_carlo import monte_carlo_simulate
import pandas as pd

returns = pd.read_csv("data/trade_returns.csv")["pnl"]

stats = monte_carlo_simulate(returns)

print(stats)
