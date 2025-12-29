"""
ml_router.py

Manages ML model inference and updates.
Supports:
- GradientBoostingClassifier fallback
- Regime-aware features
- Safe model updates
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.exceptions import NotFittedError
from fundednext_trading_system.monitoring.logger import logger

class MLRouter:
    def __init__(self, execution_flags):
        self.model = None  # Model will be loaded
        self.execution_flags = execution_flags
        self.is_trained = False

    def infer(self, features: pd.DataFrame) -> tuple | None:
        """
        Returns (side, confidence) or None
        """
        try:
            if self.model is None:
                raise NotFittedError("ML model not loaded yet")

            X = features.values
            pred_proba = self.model.predict_proba(X)[-1]  # last row
            if pred_proba.shape[0] < 2:
                # fallback if only one class
                return None

            side = "buy" if pred_proba[1] > pred_proba[0] else "sell"
            confidence = float(np.max(pred_proba))
            return (side, confidence)

        except NotFittedError:
            logger.error("❌ ML inference failed: model not fitted")
            return None
        except Exception as e:
            logger.error(f"❌ ML inference failed: {e}")
            return None

    def update_model(self, features: pd.DataFrame, df: pd.DataFrame):
        """
        Safe model update. Avoid training if insufficient classes.
        Generates binary target: 1 if next close > current close, else 0.
        """
        try:
            self.model = GradientBoostingClassifier()  # Initialize a new model
            df = df.copy()
            df['target'] = np.where(df['close'].shift(-1) > df['close'], 1, 0)
            y = df['target'][:-1]  # exclude last row
            X = features[:-1].values

            # Ensure at least 2 classes
            unique_classes = np.unique(y)
            if len(unique_classes) < 2:
                logger.warning("ML model update skipped: not enough classes to train")
                return

            self.model.fit(X, y)
            self.is_trained = True
            logger.info("✅ ML model updated successfully")

        except Exception as e:
            logger.error(f"❌ ML model update failed: {e}")
