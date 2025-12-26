from monitoring.logger import logger
from config.fundednext_rules import (
    ACCOUNT_BALANCE,
    PROFIT_TARGET,
)
from monitoring.equity_kill_switch import is_locked
from execution.mt5_account import get_equity


class ChallengePassDetector:
    def __init__(self):
        self.target_equity = ACCOUNT_BALANCE + PROFIT_TARGET

    def passed(self) -> bool:
        equity = get_equity()

        if is_locked():
            logger.warning("Challenge check failed — account locked")
            return False

        if equity >= self.target_equity:
            logger.success(
                f"🏆 CHALLENGE PASSED | Equity=${equity:.2f} "
                f"| Target=${self.target_equity:.2f}"
            )
            return True

        return False
