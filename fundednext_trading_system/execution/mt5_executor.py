import os
from datetime import datetime

from fundednext_trading_system.monitoring.profit_lock import check_profit_lock
from fundednext_trading_system.monitoring.trade_ledger import TradeRecord
from fundednext_trading_system.monitoring.pnl_tracker import record_trade
from fundednext_trading_system.monitoring.logger import logger
from fundednext_trading_system.monitoring.equity_kill_switch import (
    check_equity_limits,
    is_locked,
    get_lock_reason,
)
from fundednext_trading_system.execution.order_validator import validate_order

try:
    import MetaTrader5 as mt5
except Exception:
    mt5 = None


class MT5Executor:
    """
    Execution-only engine.
    All risk, scaling, and challenge logic lives in RiskManager.
    """

    def __init__(
        self,
        risk_manager,
        account=None,
        password=None,
        server=None,
    ):
        self.risk = risk_manager

        self.account = account or os.getenv("MT5_LOGIN")
        self.password = password or os.getenv("MT5_PASSWORD")
        self.server = server or os.getenv("MT5_SERVER")

        self.connected = False
        self._initialize()

    # =========================
    # CONNECTION
    # =========================
    def _initialize(self):
        if mt5 is None:
            logger.error("MetaTrader5 package not available")
            return

        if not mt5.initialize():
            logger.error("MT5 initialization failed")
            return

        if self.account and self.password and self.server:
            if not mt5.login(
                int(self.account),
                self.password,
                self.server,
            ):
                logger.error("MT5 login failed")
                return

        self.connected = True
        logger.info("MT5 connected successfully")

    # =========================
    # ORDER EXECUTION
    # =========================
    def place_order(
        self,
        symbol: str,
        signal: str,
        stop_loss_pips: float,
        take_profit_pips: float,
        volume: float,
    ):
        # -------------------------
        # GLOBAL SAFETY
        # -------------------------
        if not check_profit_lock():
            logger.critical("ORDER BLOCKED — PROFIT LOCK ACTIVE")
            return None

        if not check_equity_limits():
            logger.critical(
                f"ORDER BLOCKED — {get_lock_reason()}"
            )
            return None

        if not self.connected:
            logger.error("MT5 not connected")
            return None

        if not validate_order(symbol):
            logger.warning(
                f"Order blocked by validator: {symbol}"
            )
            return None

        # -------------------------
        # SYMBOL INFO
        # -------------------------
        info = mt5.symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol)

        if info is None or tick is None:
            logger.error("Symbol info unavailable")
            return None

        price = tick.ask if signal == "buy" else tick.bid
        point = info.point

        sl = (
            price - stop_loss_pips * point
            if signal == "buy"
            else price + stop_loss_pips * point
        )
        tp = (
            price + take_profit_pips * point
            if signal == "buy"
            else price - take_profit_pips * point
        )

        order_type = (
            mt5.ORDER_TYPE_BUY
            if signal == "buy"
            else mt5.ORDER_TYPE_SELL
        )

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 10,
            "magic": 777001,
            "comment": "FundedNext-Strict",
        }

        result = mt5.order_send(request)

        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(
                f"Order failed | retcode={getattr(result, 'retcode', None)}"
            )
            return None

        logger.success(
            f"ORDER EXECUTED | {symbol} | {signal.upper()} | "
            f"vol={volume} | ticket={result.order}"
        )

        return result.order

    # =========================
    # PARTIAL CLOSE
    # =========================
    def close_partial(self, ticket: int, volume: float):
        if is_locked():
            logger.critical(
                "PARTIAL CLOSE BLOCKED — EQUITY LOCK"
            )
            return None

        position = self._get_position(ticket)
        if not position:
            return None

        if volume <= 0 or volume >= position.volume:
            logger.error("Invalid partial close volume")
            return None

        return self._close_position(position, volume)

    # =========================
    # MODIFY STOP LOSS
    # =========================
    def modify_sl(self, ticket: int, new_sl: float):
        if is_locked():
            logger.critical(
                "SL MODIFICATION BLOCKED — EQUITY LOCK"
            )
            return None

        position = self._get_position(ticket)
        if not position:
            return None

        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": position.symbol,
            "position": ticket,
            "sl": new_sl,
            "tp": position.tp,
            "magic": 777001,
            "comment": "SL Update",
        }

        result = mt5.order_send(request)

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error("Stop loss modification failed")
            return None

        logger.success(
            f"SL UPDATED | {position.symbol} | {new_sl}"
        )
        return result

    # =========================
    # FULL CLOSE + FEEDBACK
    # =========================
    def close_trade(self, ticket: int):
        position = self._get_position(ticket)
        if not position:
            return None

        result = self._close_position(
            position,
            position.volume,
        )

        if not result:
            return None

        pnl = position.profit

        # -------------------------
        # RISK FEEDBACK
        # -------------------------
        if pnl < 0:
            self.risk.register_loss(abs(pnl))
        else:
            self.risk.register_profit(pnl)

        # -------------------------
        # EQUITY SYNC
        # -------------------------
        info = mt5.account_info()
        if info:
            self.risk.scaler.update_equity(info.equity)

        # -------------------------
        # LEDGER
        # -------------------------
        trade = TradeRecord(
            symbol=position.symbol,
            side=(
                "buy"
                if position.type == mt5.ORDER_TYPE_BUY
                else "sell"
            ),
            entry_price=position.price_open,
            exit_price=position.price_current,
            volume=position.volume,
            pnl=pnl,
            model_version="active",
            timestamp=datetime.utcnow(),
        )
        record_trade(trade)

        logger.success(
            f"TRADE CLOSED | {position.symbol} | PnL=${pnl:.2f}"
        )

        return result

    # =========================
    # INTERNAL HELPERS
    # =========================
    def _get_position(self, ticket: int):
        positions = mt5.positions_get(ticket=ticket)
        if not positions:
            logger.error(f"Position not found: {ticket}")
            return None
        return positions[0]

    def _close_position(self, position, volume: float):
        close_type = (
            mt5.ORDER_TYPE_SELL
            if position.type == mt5.ORDER_TYPE_BUY
            else mt5.ORDER_TYPE_BUY
        )

        tick = mt5.symbol_info_tick(position.symbol)
        price = (
            tick.bid
            if position.type == mt5.ORDER_TYPE_BUY
            else tick.ask
        )

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "position": position.ticket,
            "volume": volume,
            "type": close_type,
            "price": price,
            "deviation": 10,
            "magic": 777001,
            "comment": "Position Close",
        }

        result = mt5.order_send(request)

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error("Trade close failed")
            return None

        return result

    # =========================
    # SHUTDOWN
    # =========================
    def shutdown(self):
        if mt5:
            mt5.shutdown()
            logger.info("MT5 shutdown complete")
