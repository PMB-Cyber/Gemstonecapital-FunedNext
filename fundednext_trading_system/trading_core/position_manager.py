import datetime
from loguru import logger
from config.symbols_config import SYMBOLS_CONFIG
from trading_core.session_filter import is_friday_close_window


class PositionManager:
    def __init__(
        self,
        tp1_atr: float = 1.0,
        tp2_atr: float = 2.0,
        trail_atr: float = 1.2,
        max_trade_minutes: int = 240
    ):
        self.tp1_atr = tp1_atr
        self.tp2_atr = tp2_atr
        self.trail_atr = trail_atr
        self.max_trade_minutes = max_trade_minutes

    def manage(self, trade, current_price, atr, executor):
        """
        trade: dict from RiskManager
        executor: MT5Executor instance
        """

        symbol = trade["symbol"]
        entry = trade["entry"]
        signal = trade["signal"]
        volume = trade["volume"]

        direction = 1 if signal == "buy" else -1
        move = (current_price - entry) * direction

        tp1 = self.tp1_atr * atr
        tp2 = self.tp2_atr * atr

        # 1️⃣ Partial TP
        if not trade.get("tp1_hit") and move >= tp1:
            logger.info(f"TP1 hit → partial close {symbol}")
            executor.close_partial(trade, volume * 0.5)
            trade["tp1_hit"] = True
            trade["sl"] = entry  # BE

        # 2️⃣ ATR Trailing Stop
        if trade.get("tp1_hit"):
            new_sl = (
                current_price - self.trail_atr * atr
                if signal == "buy"
                else current_price + self.trail_atr * atr
            )
            executor.modify_sl(trade, new_sl)

        # 3️⃣ TP2 Full Exit
        if move >= tp2:
            logger.info(f"TP2 hit → closing trade {symbol}")
            executor.close_trade(trade)
            return "closed"

        # 4️⃣ Max Duration Kill
        open_time = trade.get("open_time")
        if open_time:
            age = (datetime.datetime.utcnow() - open_time).total_seconds() / 60
            if age > self.max_trade_minutes:
                logger.warning(f"Trade expired → closing {symbol}")
                executor.close_trade(trade)
                return "closed"

        # 5️⃣ Friday Safety Kill
        if is_friday_close_window():
            logger.warning(f"Friday close → closing {symbol}")
            executor.close_trade(trade)
            return "closed"

        return "active"
