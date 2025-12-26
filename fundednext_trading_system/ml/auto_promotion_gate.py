from monitoring.logger import logger
from trading_core.model_guard import promote_model_version

REQUIRED_CLEAN_SESSIONS = 5   # 🔒 SAFE DEFAULT


class AutoPromotionGate:
    def __init__(self, symbol, tracker, shadow_model_path):
        self.symbol = symbol
        self.tracker = tracker
        self.shadow_model_path = shadow_model_path

    def evaluate(self):
        clean_sessions = self.tracker.clean_sessions()

        if clean_sessions < REQUIRED_CLEAN_SESSIONS:
            logger.info(
                f"{self.symbol}: Shadow model not ready "
                f"({clean_sessions}/{REQUIRED_CLEAN_SESSIONS} clean sessions)"
            )
            return False

        logger.critical(
            f"🚀 AUTO-PROMOTION TRIGGERED | {self.symbol} | "
            f"{clean_sessions} clean sessions"
        )

        promote_model_version(self.symbol, self.shadow_model_path)
        return True
