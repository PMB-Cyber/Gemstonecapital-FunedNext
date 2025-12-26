"""
order_router.py

The ONLY module allowed to send orders to MT5.
Routes approved trade instructions to either:
- Live MT5 execution
- Shadow (simulated) execution

ABSOLUTE RULE:
- This module assumes TradeGatekeeper has already approved the trade.
"""

from typing import Optional, Dict
from datetime import datetime
import uuid

from trading_core.execution_flags import ExecutionFlags, ExecutionMode
from execution.mt5_executor import MT5Executor
from monitoring.logger import logger

# NOTE:
# Actual MT5 bindings should be injected here
# from broker.mt5_client import MT5Client


class OrderRouter:
    """
    Routes orders to live MT5 or shadow execution
    based on execution flags.
    """

    def __init__(
        self,
        execution_flags: ExecutionFlags,
        mt5_client=None,
    ):
        self.execution_flags = execution_flags
        self.mt5 = mt5_client  # Dependency injection for testability

    # =========================
    # PUBLIC ENTRY POINT
    # =========================

    def route_order(
        self,
        symbol: str,
        order_type: str,
        volume: float,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        comment: str = "",
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Routes an order based on execution permissions.

        Returns:
            dict with execution result
        """

        order_id = self._generate_order_id()
        timestamp = datetime.utcnow().isoformat()

        order_payload = {
            "order_id": order_id,
            "symbol": symbol,
            "order_type": order_type,
            "volume": volume,
            "price": price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "comment": comment,
            "metadata": metadata or {},
            "timestamp": timestamp,
        }

        # -------------------------
        # GLOBAL EXECUTION CHECK
        # -------------------------
        if not self.execution_flags.allow_any_execution():
            logger.critical("Order routing blocked: execution disabled")
            return self._reject(order_payload, "Execution disabled")

        # -------------------------
        # SHADOW ROUTING
        # -------------------------
        if self.execution_flags.allow_shadow_trading():
            logger.info(f"Shadow order routed | {order_payload}")
            return self._shadow_execute(order_payload)

        # -------------------------
        # LIVE ROUTING
        # -------------------------
        if self.execution_flags.allow_live_trading():
            if self.mt5 is None:
                logger.critical("MT5 client not injected")
                return self._reject(order_payload, "MT5 client unavailable")

            return self._live_execute(order_payload)

        # -------------------------
        # FALLBACK (SHOULD NEVER HAPPEN)
        # -------------------------
        logger.error("Order routing reached invalid execution state")
        return self._reject(order_payload, "Invalid execution state")

    # =========================
    # LIVE EXECUTION
    # =========================

    def _live_execute(self, order: Dict) -> Dict:
        """
        Sends order to MT5 with safety wrappers.
        """
        try:
            logger.info(f"Sending LIVE order | {order}")

            result = self.mt5.send_order(
                symbol=order["symbol"],
                order_type=order["order_type"],
                volume=order["volume"],
                price=order["price"],
                stop_loss=order["stop_loss"],
                take_profit=order["take_profit"],
                comment=order["comment"],
            )

            if not result.get("success"):
                logger.error(f"MT5 order failed | {result}")
                return self._reject(order, result.get("error", "MT5 error"))

            logger.info(f"Order executed LIVE | Ticket={result.get('ticket')}")
            return {
                **order,
                "status": "filled",
                "ticket": result.get("ticket"),
                "execution": "live",
            }

        except Exception as e:
            logger.exception("Live execution exception")
            return self._reject(order, str(e))

    # =========================
    # SHADOW EXECUTION
    # =========================

    def _shadow_execute(self, order: Dict) -> Dict:
        """
        Simulates execution without touching MT5.
        """
        return {
            **order,
            "status": "simulated",
            "ticket": None,
            "execution": "shadow",
        }

    # =========================
    # REJECTION HANDLING
    # =========================

    def _reject(self, order: Dict, reason: str) -> Dict:
        """
        Standardized rejection payload.
        """
        logger.warning(f"Order rejected | Reason={reason} | {order}")
        return {
            **order,
            "status": "rejected",
            "reason": reason,
            "execution": "none",
        }

    # =========================
    # UTILITIES
    # =========================

    @staticmethod
    def _generate_order_id() -> str:
        return str(uuid.uuid4())
