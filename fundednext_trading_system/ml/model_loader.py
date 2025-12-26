import os
import joblib
from loguru import logger


class ModelLoader:
    def __init__(self, model_dir="models/latest"):
        self.model_dir = model_dir

    def predict(self, symbol: str, X):
        model_path = os.path.join(self.model_dir, f"{symbol}.pkl")

        if not os.path.exists(model_path):
            logger.warning(f"No trained model found for {symbol}, skipping signal")
            return None

        try:
            model = joblib.load(model_path)
            score = model.predict_proba(X)[0][1]
            return float(score)
        except Exception as e:
            logger.error(f"Model inference failed for {symbol}: {e}")
            return None
