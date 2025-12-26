from monitoring.logger import logger

class CapitalScaler:
    """
    Capital scaling logic (growth-only, drawdown-frozen).

    Scaling Rules:
    - Scaling activates only when equity > start balance
    - Scaling freezes on ≥3% drawdown from peak
    - Scaling capped per account tier
    """

    def __init__(self, start_balance: float):
        self.start_balance = start_balance
        self.current_equity = start_balance
        self.peak_equity = start_balance

        # Account tier detection
        if start_balance <= 10_000:
            self.max_multiplier = 1.5
            self.step = 0.25
        elif start_balance <= 25_000:
            self.max_multiplier = 2.0
            self.step = 0.30
        else:
            self.max_multiplier = 2.5
            self.step = 0.40

        logger.info(
            f"CapitalScaler initialized | Start=${start_balance:.2f} "
            f"| MaxMult={self.max_multiplier:.2f}× | Step={self.step:.2f}"
        )

    # =========================
    # EQUITY UPDATE
    # =========================
    def update_equity(self, equity: float):
        if equity <= 0:
            return
        self.current_equity = equity
        self.peak_equity = max(self.peak_equity, equity)

    # =========================
    # MULTIPLIER CALCULATION
    # =========================
    def get_multiplier(self) -> float:
        if self.current_equity <= self.start_balance:
            return 1.0

        if self.in_drawdown():
            logger.warning("Capital scaling frozen — drawdown detected")
            return 1.0

        growth = (self.current_equity - self.start_balance) / self.start_balance
        steps = int(growth // self.step)
        multiplier = 1.0 + steps * self.step
        return min(multiplier, self.max_multiplier)

    # =========================
    # DRAWDOWN CHECK
    # =========================
    def in_drawdown(self) -> bool:
        return self.current_equity < self.peak_equity * 0.97
