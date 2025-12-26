import pandas as pd

df = pd.read_csv("data/trade_history.csv")

print("Trades:", len(df))
print("Win Rate:", (df.pnl > 0).mean())
print("Avg RR:", df.rr.mean())
print("Max DD:", df.equity.min())
print("Profit Factor:",
      df[df.pnl > 0].pnl.sum() / abs(df[df.pnl < 0].pnl.sum()))
