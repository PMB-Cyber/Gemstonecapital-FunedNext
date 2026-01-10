from typing import Tuple
from fundednext_trading_system.monitoring.logger import logger

from fundednext_trading_system.trading_core.execution_flags import ExecutionFlags, AccountPhase, ExecutionMode
from fundednext_trading_system.trading_core.risk_manager import RiskManager


class TradeGatekeeper:
    """
    Combines execution permissions and risk state
    to authorize or reject trade attempts.
    """

    def __init__(
        self,
        execution_flags: ExecutionFlags,
        risk_manager: RiskManager,
    ):
        self.execution_flags = execution_flags
        self.risk_manager = risk_manager

    # =========================
    # PRIMARY ENTRY POINT
    # =========================

    def authorize_trade(
        self,
        symbol: str,
        risk_amount: float,
        is_new_trade: bool = True,
    ) -> Tuple[bool, str]:
        """
        Determines whether a trade is allowed.

        Returns:
            (allowed: bool, reason: str)
        """

        # -------------------------
        # GLOBAL EXECUTION CHECK
        # -------------------------
        if not self.execution_flags.allow_any_execution():
            reason = "Execution globally disabled"
            logger.warning(f"{symbol}: {reason}")
            return False, reason

        # -------------------------
        # LIVE VS SHADOW CHECK
        # -------------------------
        if is_new_trade and not self.execution_flags.allow_live_trading():
            reason = "Live execution not permitted (shadow or disabled mode)"
            logger.info(f"{symbol}: {reason}")
            return False, reason

        # -------------------------
        # RISK HARD STOPS
        # -------------------------
        if self.risk_manager.max_loss_breached():
            reason = "Max loss limit breached"
            logger.critical(f"{symbol}: {reason}")
            self.execution_flags.disable_execution(reason)
            return False, reason

        if self.risk_manager.daily_loss_breached():
            reason = "Daily loss limit breached"
            logger.critical(f"{symbol}: {reason}")
            self.execution_flags.disable_execution(reason)
            return False, reason

        # -------------------------
        # PER-TRADE RISK CHECK
        # -------------------------
        if not self.risk_manager.validate_trade_risk(risk_amount):
            reason = f"Trade risk {risk_amount:.2f} exceeds allowed per-trade risk"
            logger.warning(f"{symbol}: {reason}")
            return False, reason

        # -------------------------
        # ACCOUNT PHASE ENFORCEMENT
        # -------------------------
        if self.execution_flags.account_phase == AccountPhase.FUNDED:
            if not self.execution_flags.allow_live_trading():
                reason = "Funded account but live trading disabled"
                logger.warning(f"{symbol}: {reason}")
                return False, reason

        # -------------------------
        # FINAL APPROVAL
        # -------------------------
        logger.info(f"Trade approved | Symbol={symbol} | Risk={risk_amount:.2f}")
        return True, "Approved"

    # =========================
    # POSITION MANAGEMENT
    # =========================

    def authorize_position_management(self) -> bool:
        """
        Determines whether existing positions
        may be modified or closed.
        """
        if not self.execution_flags.allow_any_execution():
            logger.warning("Position management blocked: execution disabled")
            return False

        return True

    # =========================
    # EMERGENCY CONTROLS
    # =========================

    def emergency_kill(self, reason: str):
        """
        Immediately disables all execution.
        """
        logger.critical(f"EMERGENCY KILL TRIGGERED: {reason}")
        self.execution_flags.disable_execution(reason)

    # =========================
    # DEBUG / MONITORING
    # =========================

    def snapshot(self) -> dict:
        """
        Returns a combined execution + risk snapshot.
        """
        return {
            "execution_flags": self.execution_flags.snapshot(),
            "risk_state": self.risk_manager.snapshot(),
        }
