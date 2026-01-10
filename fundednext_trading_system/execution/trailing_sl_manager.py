import MetaTrader5 as mt5
import pandas as pd
from fundednext_trading_system.monitoring.logger import logger


class TrailingSLManager:
    def __init__(
        self,
        breakeven_r=1.0,
        trail_start_r=1.5,
        atr_period=14,
        atr_multiplier=1.2,
    ):
        self.breakeven_r = breakeven_r
        self.trail_start_r = trail_start_r
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self._active_symbols = set()

    def _calculate_atr(self, df: pd.DataFrame) -> float:
        """Calculate ATR from high, low, close data"""
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift()).abs()
        low_close = (df["low"] - df["close"].shift()).abs()

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(self.atr_period).mean().iloc[-1]
        return atr if pd.notna(atr) else 0

    def manage(self, symbol: str, df: pd.DataFrame):
        positions = mt5.positions_get(symbol=symbol)
        if not positions:
            return

        atr = self._calculate_atr(df)
        if atr <= 0:
            return

        self._active_symbols.add(symbol)

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return

        for pos in positions:
            entry = pos.price_open
            sl = pos.sl
            tp = pos.tp
            direction = pos.type

            # Current price based on direction
            current_price = tick.bid if direction == mt5.ORDER_TYPE_BUY else tick.ask

            # Current risk
            risk = abs(entry - sl) if sl > 0 else atr * self.atr_multiplier
            if risk <= 0:
                continue

            # Current R-multiple
            r_multiple = (
                (current_price - entry) / risk
                if direction == mt5.ORDER_TYPE_BUY
                else (entry - current_price) / risk
            )

            # -------------------------
            # BREAKEVEN MOVE
            # -------------------------
            new_sl = sl
            if r_multiple >= self.breakeven_r:
                new_sl = entry

            # -------------------------
            # TRAILING AFTER trail_start_r
            # -------------------------
            if r_multiple >= self.trail_start_r:
                if direction == mt5.ORDER_TYPE_BUY:
                    new_sl = current_price - (atr * self.atr_multiplier)
                else:
                    new_sl = current_price + (atr * self.atr_multiplier)

            # Prevent SL worsening
            if direction == mt5.ORDER_TYPE_BUY and new_sl <= sl:
                continue
            if direction == mt5.ORDER_TYPE_SELL and new_sl >= sl:
                continue

            # Prepare request
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": pos.ticket,
                "sl": round(new_sl, 5),
                "tp": tp,
                "symbol": symbol,
                "magic": pos.magic,
                "comment": "TRAILING SL MANAGER",
            }

            # Send request
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.success(
                    f"🔁 Trailing SL updated | {symbol} | ticket={pos.ticket} | new_sl={new_sl:.5f}"
                )
            else:
                logger.warning(
                    f"❌ Failed SL update | {symbol} | ticket={pos.ticket} | retcode={result.retcode}"
                )

    # =========================
    # For Heartbeat Monitoring
    # =========================
    def active_symbols(self):
        return list(self._active_symbols)

    def current_sl(self, symbol: str):
        positions = mt5.positions_get(symbol=symbol)
        if not positions:
            return "-"
        sl_list = []
        for pos in positions:
            sl_list.append(f"Ticket {pos.ticket}: SL={pos.sl}")
        return "; ".join(sl_list) if sl_list else "-"
