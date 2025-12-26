"""
ml_router.py

Responsible for routing ML operations:
- Inference for signal generation
- Shadow model training (optional)
- Freeze ML when in funded mode

ABSOLUTE RULES:
1. No training on funded accounts.
2. Shadow models never affect live trades.
3. Inference can continue if allowed.
"""

from typing import Any, Dict
from monitoring.logger import logger
from trading_core.execution_flags import ExecutionFlags, MLMode
from monitoring.logger import logger


class MLRouter:
    """
    Central ML routing logic.
    Ensures proper handling of frozen, shadow, and training modes.
    """

    def __init__(self, execution_flags: ExecutionFlags):
        self.execution_flags = execution_flags
        self.shadow_models = {}  # key: model_name, value: model object
        self.frozen_model = None  # production model (frozen)

    # =========================
    # LOAD MODELS
    # =========================

    def load_frozen_model(self, model: Any):
        """
        Load the production model (frozen).
        """
        self.frozen_model = model
        logger.info("Frozen production model loaded")

    def register_shadow_model(self, name: str, model: Any):
        """
        Register a shadow model for experimentation/training.
        """
        self.shadow_models[name] = model
        logger.info(f"Shadow model registered: {name}")

    # =========================
    # INFERENCE
    # =========================

    def infer(self, features: Dict, model_name: str = None) -> Any:
        """
        Runs ML inference.
        If model_name is provided, uses that model; otherwise uses frozen model.
        """
        if not self.execution_flags.allow_ml_inference():
            logger.warning("ML inference blocked by execution flags")
            return None

        if model_name:
            model = self.shadow_models.get(model_name)
            if model is None:
                logger.warning(f"Shadow model '{model_name}' not found")
                return None
        else:
            model = self.frozen_model
            if model is None:
                logger.warning("Frozen model not loaded")
                return None

        try:
            prediction = model.predict(features)
            logger.debug(f"ML inference result: {prediction}")
            return prediction
        except Exception as e:
            logger.exception(f"ML inference failed: {e}")
            return None

    # =========================
    # TRAINING (CHALLENGE ONLY)
    # =========================

    def train_shadow_model(self, model_name: str, features: Dict, labels: Any):
        """
        Trains a shadow model if allowed.
        Shadow models never impact live trading.
        """
        if not self.execution_flags.allow_ml_training():
            logger.warning("ML training blocked by execution flags")
            return False

        model = self.shadow_models.get(model_name)
        if model is None:
            logger.warning(f"Shadow model '{model_name}' not found for training")
            return False

        try:
            model.fit(features, labels)
            logger.info(f"Shadow model '{model_name}' trained successfully")
            return True
        except Exception as e:
            logger.exception(f"Shadow model training failed: {e}")
            return False

    # =========================
    # SNAPSHOT / MONITORING
    # =========================

    def snapshot(self) -> Dict:
        """
        Returns current ML router state for monitoring/logging.
        """
        return {
            "frozen_model_loaded": self.frozen_model is not None,
            "shadow_models": list(self.shadow_models.keys()),
            "ml_mode": self.execution_flags.ml_mode.value,
        }
