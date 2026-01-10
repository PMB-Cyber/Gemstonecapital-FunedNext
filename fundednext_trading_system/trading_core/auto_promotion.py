from fundednext_trading_system.trading_core.challenge_pass_detector import ChallengePassDetector
from fundednext_trading_system.trading_core.challenge_lock import lock_challenge, is_challenge_locked
from fundednext_trading_system.monitoring.logger import logger


def run_auto_promotion():
    if is_challenge_locked():
        return

    detector = ChallengePassDetector()

    if detector.passed():
        lock_challenge()
        logger.success(
            "🎉 Challenge completed — "
            "restart system in FUNDED mode"
        )
