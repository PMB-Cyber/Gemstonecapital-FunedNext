from datetime import datetime
from fundednext_trading_system.monitoring.logger import logger
from fundednext_trading_system.trading_core.risk_manager import RiskManager
from fundednext_trading_system.trading_core.execution_flags import ExecutionFlags, AccountPhase, ExecutionMode, MLMode


class SessionController:
    """
    Handles daily sessions, account phase transitions,
    and maintenance for FundedNext-compliant trading.
    """

    def __init__(self, execution_flags: ExecutionFlags, risk_manager: RiskManager, auto_promote: bool = True):
        self.execution_flags = execution_flags
        self.risk_manager = risk_manager
        self.auto_promote = auto_promote
        self.last_reset_date = datetime.utcnow().date()

    # =========================
    # DAILY RESET
    # =========================
    def reset_daily_session(self):
        today = datetime.utcnow().date()
        if today != self.last_reset_date:
            logger.info(f"🔄 Daily session reset | {today}")
            self.risk_manager._reset_daily_if_new_day()
            self.last_reset_date = today

    # =========================
    # ACCOUNT PHASE PROMOTION
    # =========================
    def update_account_phase(self):
        if not self.auto_promote:
            return

        if self.execution_flags.account_phase != AccountPhase.CHALLENGE:
            return

        if self._criteria_for_funded():
            self._promote_to_funded()

    def _criteria_for_funded(self) -> bool:
        if self.risk_manager.max_loss_breached():
            return False
        if self.risk_manager.daily_loss_breached():
            return False
        if not self.risk_manager.challenge_passed:
            return False
        return True

    def _promote_to_funded(self):
        logger.success("🎉 Challenge PASSED — Promoting to FUNDED account")

        self.execution_flags.account_phase = AccountPhase.FUNDED
        self.execution_flags.execution_mode = ExecutionMode.LIVE
        self.execution_flags.ml_mode = MLMode.SHADOW

        self.execution_flags.clear_execution_blocks()

    # =========================
    # DAILY MAINTENANCE LOOP
    # =========================
    def daily_maintenance(self):
        self.reset_daily_session()
        self.update_account_phase()
        self.log_snapshot()

    # =========================
    # SNAPSHOT / MONITORING
    # =========================
    def log_snapshot(self):
        snapshot = {
            "timestamp": datetime.utcnow().isoformat(),
            "account_phase": self.execution_flags.account_phase.value,
            "execution_mode": self.execution_flags.execution_mode.value,
            "ml_mode": self.execution_flags.ml_mode.value,
            "daily_loss": round(self.risk_manager.daily_loss, 2),
            "max_loss_breached": self.risk_manager.max_loss_breached(),
        }
        logger.info(f"📸 Session snapshot | {snapshot}")
