"""
execution_flags.py

Centralized execution and behavior flags for the live MT5 trading system.
This file determines what the system is allowed to do at runtime depending
on account phase, risk state, and ML lifecycle state.

IMPORTANT:
- This file should NEVER contain trading logic
- Only high-level execution permissions and mode switches
"""

from enum import Enum
from datetime import datetime


# =========================
# ACCOUNT & EXECUTION MODES
# =========================

class AccountPhase(Enum):
    CHALLENGE = "challenge"
    FUNDED = "funded"


class ExecutionMode(Enum):
    LIVE = "live"           # Sends real MT5 orders
    SHADOW = "shadow"       # Simulates execution only
    DISABLED = "disabled"   # No execution allowed


# =========================
# ML MODES
# =========================

class MLMode(Enum):
    FROZEN = "frozen"       # No training, inference only
    TRAINING = "training"  # Live learning (challenge only)
    SHADOW = "shadow"       # Trains but does not affect trades
    OFF = "off"


# =========================
# EXECUTION FLAGS OBJECT
# =========================

class ExecutionFlags:
    """
    Runtime execution control flags.
    Initialized once at startup and updated only on
    phase transitions or risk events.
    """

    def __init__(
        self,
        account_phase: AccountPhase,
        execution_mode: ExecutionMode,
        ml_mode: MLMode,
    ):
        self.account_phase = account_phase
        self.execution_mode = execution_mode
        self.ml_mode = ml_mode

        self.last_updated = datetime.utcnow()

    # =========================
    # SAFETY CHECKS
    # =========================

    def allow_live_trading(self) -> bool:
        """
        Determines whether MT5 orders are allowed to be sent.
        """
        return self.execution_mode == ExecutionMode.LIVE

    def allow_shadow_trading(self) -> bool:
        """
        Determines whether shadow execution is active.
        """
        return self.execution_mode == ExecutionMode.SHADOW

    def allow_any_execution(self) -> bool:
        """
        Global execution gate.
        """
        return self.execution_mode != ExecutionMode.DISABLED

    def allow_ml_training(self) -> bool:
        """
        Determines whether ML training is allowed.
        """
        return self.ml_mode in (MLMode.TRAINING, MLMode.SHADOW)

    def allow_ml_inference(self) -> bool:
        """
        Determines whether ML inference is allowed.
        """
        return self.ml_mode != MLMode.OFF

    # =========================
    # PHASE TRANSITIONS
    # =========================

    def switch_to_funded(self):
        """
        Enforces FundedNext-funded rules:
        - Live trading enabled
        - ML frozen
        - Shadow models allowed
        """
        self.account_phase = AccountPhase.FUNDED
        self.execution_mode = ExecutionMode.LIVE
        self.ml_mode = MLMode.FROZEN
        self._touch()

    def switch_to_challenge(self):
        """
        Enforces challenge-phase behavior:
        - Live trading enabled
        - ML training allowed
        """
        self.account_phase = AccountPhase.CHALLENGE
        self.execution_mode = ExecutionMode.LIVE
        self.ml_mode = MLMode.TRAINING
        self._touch()

    # =========================
    # EMERGENCY & RISK CONTROLS
    # =========================

    def disable_execution(self, reason: str = ""):
        """
        Hard kill-switch for execution.
        Used for max loss breach, system faults, or manual intervention.
        """
        self.execution_mode = ExecutionMode.DISABLED
        self._touch()

    def enable_shadow_mode(self):
        """
        Enables shadow trading only (no real orders).
        """
        self.execution_mode = ExecutionMode.SHADOW
        self._touch()

    # =========================
    # INTERNAL
    # =========================

    def _touch(self):
        self.last_updated = datetime.utcnow()

    # =========================
    # DEBUG / LOGGING
    # =========================

    def snapshot(self) -> dict:
        """
        Returns a serializable snapshot for logging and monitoring.
        """
        return {
            "account_phase": self.account_phase.value,
            "execution_mode": self.execution_mode.value,
            "ml_mode": self.ml_mode.value,
            "last_updated": self.last_updated.isoformat(),
        }
