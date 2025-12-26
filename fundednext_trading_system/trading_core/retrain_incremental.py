"""
Offline ONLY — never imported by live system
"""
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from joblib import dump

DATA_PATH = "data/trade_history.csv"
OUTPUT_MODEL = "models/model_candidate.joblib"

df = pd.read_csv(DATA_PATH)

X = df.drop(columns=["outcome"])
y = df["outcome"]

model = GradientBoostingClassifier()
model.fit(X, y)

dump(model, OUTPUT_MODEL)
print("Candidate model trained")
