import pandas as pd

df = pd.read_csv("ml/training/EURUSD_dataset.csv")
print("COLUMNS:", list(df.columns))
print("ROWS:", len(df))
