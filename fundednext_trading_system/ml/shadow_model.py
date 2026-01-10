import os
import joblib
from fundednext_trading_system.monitoring.logger import logger

CANDIDATE_DIR = "models/candidates"


class ShadowModel:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.model = None
        self.model_path = self._find_latest_candidate()

        if self.model_path:
            self.model = joblib.load(self.model_path)
            logger.info(
                f"🕶 Shadow model loaded | {symbol} | {self.model_path}"
            )

    def _find_latest_candidate(self):
        if not os.path.exists(CANDIDATE_DIR):
            return None

        files = [
            f for f in os.listdir(CANDIDATE_DIR)
            if f.startswith(self.symbol) and f.endswith(".pkl")
        ]

        if not files:
            return None

        files.sort(reverse=True)
        return os.path.join(CANDIDATE_DIR, files[0])

    def predict(self, X):
        if not self.model:
            return None
        return self.model.predict_proba(X)[0][1]
