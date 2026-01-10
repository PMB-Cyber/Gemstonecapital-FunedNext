from fundednext_trading_system.ml.shadow_model_loader import ShadowModelLoader
from fundednext_trading_system.monitoring.logger import logger

class ShadowSignalEngine:
    def __init__(self, model_path: str, confidence_threshold=0.7):
        self.threshold = confidence_threshold
        self.loader = ShadowModelLoader(model_path)

    def generate_signal(self, X):
        score = self.loader.predict(X)[0]

        if score >= self.threshold:
            return "buy", score

        if score <= (1 - self.threshold):
            return "sell", score

        return None
