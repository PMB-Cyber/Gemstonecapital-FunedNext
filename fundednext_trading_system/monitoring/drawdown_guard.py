import json
from datetime import date
from pathlib import Path
from config.risk_limits import (
    MAX_DAILY_LOSS_PCT,
    MAX_TOTAL_DRAWDOWN_PCT,
    ACCOUNT_EQUITY_START,
)
from monitoring.logger import logger

STATE_FILE = Path("monitoring/.drawdown_state.json")


class DrawdownGuard:
    def __init__(self):
        self.state = self._load_state()

    def _load_state(self):
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text())

        return {
            "start_equity": ACCOUNT_EQUITY_START,
            "daily_pnl": 0.0,
            "total_pnl": 0.0,
            "last_day": str(date.today()),
            "locked": False,
        }

    def _save(self):
        STATE_FILE.write_text(json.dumps(self.state, indent=2))

    def update_pnl(self, pnl: float):
        today = str(date.today())

        if self.state["last_day"] != today:
            self.state["daily_pnl"] = 0.0
            self.state["last_day"] = today

        self.state["daily_pnl"] += pnl
        self.state["total_pnl"] += pnl

        self._evaluate_limits()
        self._save()

    def _evaluate_limits(self):
        daily_loss_pct = abs(self.state["daily_pnl"]) / self.state["start_equity"] * 100
        total_dd_pct = abs(self.state["total_pnl"]) / self.state["start_equity"] * 100

        if self.state["daily_pnl"] < 0 and daily_loss_pct >= MAX_DAILY_LOSS_PCT:
            self._lock("DAILY LOSS LIMIT HIT")

        if self.state["total_pnl"] < 0 and total_dd_pct >= MAX_TOTAL_DRAWDOWN_PCT:
            self._lock("TOTAL DRAWDOWN LIMIT HIT")

    def _lock(self, reason):
        if not self.state["locked"]:
            logger.critical(f"🛑 KILL SWITCH ACTIVATED — {reason}")
            self.state["locked"] = True

    def is_locked(self):
        return self.state["locked"]
