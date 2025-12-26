import joblib
import os

class ShadowModelLoader:
    def __init__(self, model_path: str):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Shadow model not found: {model_path}")

        self.model = joblib.load(model_path)

    def predict(self, X):
        return self.model.predict_proba(X)[:, 1]
