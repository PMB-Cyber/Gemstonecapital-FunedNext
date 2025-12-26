from enum import Enum
from monitoring.logger import logger  # Ensure logger is imported

class AccountPhase(Enum):
    CHALLENGE = "challenge"
    FUNDED = "funded"

class ExecutionMode(Enum):
    SHADOW = "shadow"
    LIVE = "live"

class MLMode(Enum):
    TRAINING = "training"
    INFERENCE = "inference"

class ExecutionFlags:
    def __init__(self, account_phase: AccountPhase, execution_mode: ExecutionMode, ml_mode: MLMode):
        self.account_phase = account_phase
        self.execution_mode = execution_mode
        self.ml_mode = ml_mode

    def allow_any_execution(self):
        """
        Determines if the system allows any execution based on the current execution phase.
        Logs the decision for better clarity.
        """
        if self.execution_mode == ExecutionMode.LIVE and self.account_phase == AccountPhase.FUNDED:
            logger.debug(f"Execution allowed: LIVE mode with FUNDED account.")
            return True
        elif self.execution_mode == ExecutionMode.SHADOW:
            logger.debug(f"Execution denied: SHADOW mode.")
            return False
        logger.debug(f"Execution denied: Unknown configuration.")
        return False

    def allow_live_trading(self):
        """
        Checks if live trading is permitted.
        Logs the decision for better clarity.
        """
        if self.execution_mode == ExecutionMode.LIVE and self.account_phase == AccountPhase.FUNDED:
            logger.debug("Live trading allowed.")
            return True
        logger.debug("Live trading not allowed.")
        return False

    def disable_execution(self, reason: str):
        """
        Disable execution entirely, typically triggered in case of errors or risk limits.
        Logs the reason for disabling execution.
        """
        logger.critical(f"Execution disabled due to: {reason}")
        self.execution_mode = ExecutionMode.SHADOW  # Switch to SHADOW mode to prevent trades
        logger.info(f"Execution mode set to SHADOW due to: {reason}")

# =========================
# GLOBAL SINGLETON
# =========================
execution_flags_singleton = ExecutionFlags(
    account_phase=AccountPhase.CHALLENGE,
    execution_mode=ExecutionMode.SHADOW,
    ml_mode=MLMode.TRAINING
)
