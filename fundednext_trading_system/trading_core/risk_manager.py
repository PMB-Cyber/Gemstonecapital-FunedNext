from datetime import date
from fundednext_trading_system.monitoring.logger import logger
from fundednext_trading_system.config.settings import CURRENT_RULES, CORRELATION_THRESHOLD
from fundednext_trading_system.trading_core.capital_scaler import CapitalScaler
from fundednext_trading_system.trading_core.correlation_manager import CorrelationManager


class RiskManager:
    """
    Manages account risk, position sizing, loss/profit tracking,
    and capital scaling.

    Fully compatible with FundedNext rules.
    """

    def __init__(self):
        self.correlation_manager = CorrelationManager()
        self.start_balance = CURRENT_RULES["ACCOUNT_BALANCE"]
        self.current_equity = self.start_balance

        self.daily_loss = 0.0
        self.total_loss = 0.0
        self.last_day = date.today()

        self.scaler = CapitalScaler(self.start_balance)

        # Used by SessionController for promotion logic
        self.challenge_passed = False

        logger.info(
            f"RiskManager initialized | "
            f"Account=${self.start_balance:.2f} | "
            f"DailyLimit=${CURRENT_RULES['DAILY_LOSS_LIMIT']:.2f} | "
            f"MaxLimit=${CURRENT_RULES['MAX_LOSS_LIMIT']:.2f}"
        )

    # =========================
    # EQUITY SYNC
    # =========================
    def update_equity(self, equity: float):
        if equity <= 0:
            return

        self.current_equity = equity
        self.scaler.update_equity(equity)

        logger.debug(
            f"Equity synced | Current=${equity:.2f} | "
            f"Peak=${self.scaler.peak_equity:.2f}"
        )

    # =========================
    # DAILY RESET
    # =========================
    def _reset_daily_if_new_day(self):
        today = date.today()
        if today != self.last_day:
            logger.info(
                f"New trading day — resetting daily loss "
                f"(prev=${self.daily_loss:.2f})"
            )
            self.daily_loss = 0.0
            self.last_day = today

    # =========================
    # PRE-TRADE RISK CHECKS
    # =========================
    def can_open_trade(self, risk_amount: float, symbol: str, open_positions: list) -> bool:
        self._reset_daily_if_new_day()

        if not self._validate_trade_risk(risk_amount):
            return False

        if not self._validate_correlation(symbol, open_positions):
            return False

        return True

    def _validate_correlation(self, symbol: str, open_positions: list) -> bool:
        if not self.correlation_manager.matrix_ready:
            logger.warning("Correlation matrix not ready, skipping check.")
            return True

        if not open_positions:
            return True # No open positions, no correlation to check

        for position in open_positions:
            correlation = self.correlation_manager.get_correlation(symbol, position.symbol)
            if abs(correlation) > CORRELATION_THRESHOLD:
                logger.warning(
                    f"Trade blocked for {symbol} due to high correlation ({correlation:.2f}) "
                    f"with open position on {position.symbol}."
                )
                return False

        return True

    def _validate_trade_risk(self, risk_amount: float) -> bool:
        if risk_amount <= 0:
            logger.warning("Trade blocked — zero or negative risk")
            return False

        if risk_amount > CURRENT_RULES["MAX_RISK_PER_TRADE"]:
            logger.warning(
                f"Trade blocked — risk ${risk_amount:.2f} "
                f"exceeds max per trade ${CURRENT_RULES['MAX_RISK_PER_TRADE']:.2f}"
            )
            return False

        if self.daily_loss + risk_amount > CURRENT_RULES["DAILY_LOSS_LIMIT"]:
            logger.critical(
                f"Trade blocked — daily loss limit breach | "
                f"Daily=${self.daily_loss:.2f}"
            )
            return False

        if self.total_loss + risk_amount > CURRENT_RULES["MAX_LOSS_LIMIT"]:
            logger.critical(
                f"Trade blocked — max loss limit breach | "
                f"Total=${self.total_loss:.2f}"
            )
            return False

        return True

    # =========================
    # POSITION SIZING
    # =========================
    def position_size(
        self,
        symbol: str,
        stop_loss_pips: float,
        pip_value: float = 10.0
    ) -> float:

        if stop_loss_pips <= 0:
            logger.error(f"{symbol}: invalid stop loss pips")
            return 0.0

        self._reset_daily_if_new_day()

        remaining_daily = max(0.0, CURRENT_RULES["DAILY_LOSS_LIMIT"] - self.daily_loss)
        remaining_total = max(0.0, CURRENT_RULES["MAX_LOSS_LIMIT"] - self.total_loss)

        base_risk = min(
            CURRENT_RULES["MAX_RISK_PER_TRADE"],
            remaining_daily,
            remaining_total
        )

        if base_risk <= 0:
            logger.critical(f"{symbol}: no remaining risk budget")
            return 0.0

        # Capital scaling (growth-only, frozen on drawdown)
        multiplier = self.scaler.get_multiplier()
        scaled_risk = base_risk * multiplier

        # Hard safety caps (prop-firm safe)
        scaled_risk = min(
            scaled_risk,
            CURRENT_RULES["MAX_RISK_PER_TRADE"],
            remaining_daily,
            remaining_total
        )

        if scaled_risk <= 0:
            logger.warning(f"{symbol}: scaled risk reduced to zero")
            return 0.0

        volume = scaled_risk / (stop_loss_pips * pip_value)

        logger.info(
            f"{symbol}: position size | "
            f"base=${base_risk:.2f} | "
            f"mult={multiplier:.2f}× | "
            f"final=${scaled_risk:.2f} | "
            f"vol={volume:.3f}"
        )

        return round(volume, 3)

    # =========================
    # LOSS / PROFIT TRACKING
    # =========================
    def register_loss(self, loss_amount: float):
        if loss_amount <= 0:
            return

        self._reset_daily_if_new_day()
        self.daily_loss += loss_amount
        self.total_loss += loss_amount

        logger.warning(
            f"Loss registered | "
            f"Daily=${self.daily_loss:.2f} | "
            f"Total=${self.total_loss:.2f}"
        )

    def register_profit(self, profit_amount: float):
        """
        Profits do NOT offset losses (FundedNext compliant)
        """
        if profit_amount <= 0:
            return

        logger.info(
            f"Profit registered (non-offset) | ${profit_amount:.2f}"
        )

    # =========================
    # HARD STOPS
    # =========================
    def hard_stop_triggered(self) -> bool:
        triggered = (
            self.daily_loss >= CURRENT_RULES["DAILY_LOSS_LIMIT"]
            or self.total_loss >= CURRENT_RULES["MAX_LOSS_LIMIT"]
        )
        if triggered:
            logger.critical(
                "🚨 HARD STOP TRIGGERED — loss limits exceeded"
            )
        return triggered

    def max_loss_breached(self) -> bool:
        return self.total_loss >= CURRENT_RULES["MAX_LOSS_LIMIT"]

    def daily_loss_breached(self) -> bool:
        return self.daily_loss >= CURRENT_RULES["DAILY_LOSS_LIMIT"]

    # =========================
    # STATUS / HEARTBEAT
    # =========================
    def get_status(self) -> dict:
        """
        Lightweight status snapshot for monitoring & heartbeat.
        """
        return {
            "equity": round(self.current_equity, 2),
            "daily_loss": round(self.daily_loss, 2),
            "total_loss": round(self.total_loss, 2),
            "daily_limit": CURRENT_RULES["DAILY_LOSS_LIMIT"],
            "max_limit": CURRENT_RULES["MAX_LOSS_LIMIT"],
            "hard_stop": self.hard_stop_triggered(),
        }

    # =========================
    # BALANCE / EQUITY ACCESS
    # =========================
    def current_balance(self) -> float:
        """
        Returns the current equity/balance.
        """
        return self.current_equity

    @property
    def balance(self) -> float:
        """
        Property alias for current_balance(), used by orchestrator/heartbeat.
        """
        return self.current_equity
