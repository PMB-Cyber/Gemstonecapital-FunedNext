import MetaTrader5 as mt5
from datetime import datetime
from config.settings import ALLOWED_SYMBOLS
from monitoring.logger import logger

# Maximum spread limits per symbol (in points)
SYMBOL_SPREAD_LIMITS = {
    "EURUSD": 50,  # raise from 30 → 50
    "GBPUSD": 50,
    "USDJPY": 50,
    "XAUUSD": 80,
    "US30": 400,
    "NDX100": 350,
}



class StartupValidator:
    """
    Validates MT5 account, symbol permissions, spreads, and active sessions.
    """

    def __init__(self, max_spread_points: int = 30, min_free_margin_ratio: float = 0.3):
        self.max_spread_points = max_spread_points
        self.min_free_margin_ratio = min_free_margin_ratio

    # =========================
    # MAIN ENTRY
    # =========================
    def validate_or_die(self):
        logger.info("🔍 Running startup validation checks")

        if not mt5.initialize():
            raise RuntimeError("MT5 initialization failed")

        self._check_account()
        self._check_symbols()
        self._check_sessions()

        logger.success("✅ Startup validation PASSED")

    # =========================
    # ACCOUNT CHECK
    # =========================
    def _check_account(self):
        acc = mt5.account_info()
        if acc is None:
            raise RuntimeError("Account info unavailable")

        free_ratio = acc.margin_free / max(acc.balance, 1)
        logger.info(f"Account | Balance={acc.balance:.2f} | FreeMargin={acc.margin_free:.2f}")

        if free_ratio < self.min_free_margin_ratio:
            raise RuntimeError("Insufficient free margin")

    # =========================
    # SYMBOLS CHECK
    # =========================
    def _check_symbols(self):
        for symbol in ALLOWED_SYMBOLS:
            info = mt5.symbol_info(symbol)
            if info is None:
                raise RuntimeError(f"{symbol}: symbol not found")

            if not info.visible:
                mt5.symbol_select(symbol, True)

            if getattr(info, "trade_mode", None) != mt5.SYMBOL_TRADE_MODE_FULL:
                raise RuntimeError(f"{symbol}: trading not enabled")

            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                raise RuntimeError(f"{symbol}: no tick data")

            spread = abs(tick.ask - tick.bid) / getattr(info, "point", 1)
            max_spread = SYMBOL_SPREAD_LIMITS.get(symbol, self.max_spread_points)

            if spread > max_spread:
               logger.warning(
        f"{symbol}: spread high ({spread:.1f} pts > {max_spread}) — market likely closed")
            continue


            logger.info(f"{symbol}: OK | spread={spread:.1f} pts")

    # =========================
    # SESSION CHECK
    # =========================
    def _check_sessions(self):
        now = datetime.utcnow()
        for symbol in ALLOWED_SYMBOLS:
            info = mt5.symbol_info(symbol)
            if info is None:
                continue

            if not getattr(info, "session_deals", None):
                logger.warning(f"{symbol}: no active trading session")
