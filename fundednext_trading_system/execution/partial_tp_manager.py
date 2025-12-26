import MetaTrader5 as mt5
import pandas as pd
from monitoring.logger import logger


class PartialTPManager:
    def __init__(
        self,
        tp_multipliers=(1.0, 2.0),  # Multiples of ATR
        close_percents=(0.3, 0.3),
        atr_period=14,
        atr_multiplier=1.2,
    ):
        self.tp_multipliers = tp_multipliers
        self.close_percents = close_percents
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.handled = set()  # (ticket, multiplier)
        self._active_symbols = set()

    def _calculate_atr(self, df: pd.DataFrame) -> float:
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

        for pos in positions:
            entry = pos.price_open
            current = pos.price_current
            sl = pos.sl
            volume = pos.volume
            ticket = pos.ticket

            if sl <= 0:
                continue

            risk = abs(entry - sl) or (atr * self.atr_multiplier)

            rr = (
                (current - entry) / risk
                if pos.type == mt5.ORDER_TYPE_BUY
                else (entry - current) / risk
            )

            for multiplier, pct in zip(self.tp_multipliers, self.close_percents):
                key = (ticket, multiplier)
                tp_threshold = multiplier * atr

                if rr >= tp_threshold and key not in self.handled:
                    close_volume = round(volume * pct, 2)
                    if close_volume <= 0:
                        continue
                    self._partial_close(pos, close_volume)
                    self.handled.add(key)

    def _partial_close(self, pos, volume):
        close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        tick = mt5.symbol_info_tick(pos.symbol)
        price = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "position": pos.ticket,
            "volume": volume,
            "type": close_type,
            "price": price,
            "deviation": 10,
            "magic": 777001,
            "comment": "PARTIAL TP",
        }

        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.success(f"✅ PARTIAL TP executed | {pos.symbol} | vol={volume}")
        else:
            logger.error(f"❌ Partial TP failed | ticket={pos.ticket} | retcode={result.retcode}")

    # =========================
    # For Heartbeat Monitoring
    # =========================
    def active_symbols(self):
        return list(self._active_symbols)

    def status(self, symbol: str):
        positions = mt5.positions_get(symbol=symbol)
        if not positions:
            return "-"
        status_list = []
        for pos in positions:
            levels_hit = [
                multiplier for (ticket, multiplier) in self.handled if ticket == pos.ticket
            ]
            status_list.append(f"Ticket {pos.ticket}: TP levels hit={levels_hit}")
        return "; ".join(status_list) if status_list else "-"
