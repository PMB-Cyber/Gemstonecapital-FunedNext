from fundednext_trading_system.config.settings import ENVIRONMENT
if ENVIRONMENT != "production":
    from fundednext_trading_system.MetaTrader5 import MetaTrader5 as mt5
else:
    import MetaTrader5 as mt5
import pandas as pd
from fundednext_trading_system.monitoring.logger import logger


from fundednext_trading_system.config.settings import SYMBOL_PARAMS

class PartialTPManager:
    def __init__(self):
        self.handled = set()  # (ticket, multiplier)
        self._active_symbols = set()

    def _get_params(self, symbol: str) -> dict:
        return {**SYMBOL_PARAMS["DEFAULT"], **SYMBOL_PARAMS.get(symbol, {})}

    def _calculate_atr(self, df: pd.DataFrame, atr_period: int) -> float:
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift()).abs()
        low_close = (df["low"] - df["close"].shift()).abs()

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(atr_period).mean().iloc[-1]
        return atr if pd.notna(atr) else 0

    def manage(self, symbol: str, df: pd.DataFrame):
        params = self._get_params(symbol)
        atr_period = params["ATR_PERIOD"]
        atr_multiplier = params["ATR_SL_MULTIPLIER"]
        tp_multipliers = params["ATR_TP_MULTIPLIERS"]
        close_percents = params["TP_CLOSE_PERCENTS"]

        positions = mt5.positions_get(symbol=symbol)
        if not positions:
            return

        atr = self._calculate_atr(df, atr_period)
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
