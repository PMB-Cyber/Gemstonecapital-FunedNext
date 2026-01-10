import json
import os
from datetime import date
from fundednext_trading_system.monitoring.logger import logger

STATE_FILE = "ml/shadow_state.json"


class ShadowStatsTracker:
    def __init__(self, symbol):
        self.symbol = symbol
        self.state = self._load_state()

    def _load_state(self):
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        return {}

    def _save(self):
        with open(STATE_FILE, "w") as f:
            json.dump(self.state, f, indent=2)

    def record(self, live_score, shadow_score):
        today = str(date.today())

        sym = self.state.setdefault(self.symbol, {})
        session = sym.setdefault(today, {
            "trades": 0,
            "agree": 0,
            "diverge": 0
        })

        session["trades"] += 1

        if abs(live_score - shadow_score) <= 0.15:
            session["agree"] += 1
        else:
            session["diverge"] += 1

        self._save()

    def clean_sessions(self, min_agreement=0.7):
        sym = self.state.get(self.symbol, {})
        clean = 0

        for day, data in sym.items():
            if data["trades"] < 10:
                continue
            agree_ratio = data["agree"] / data["trades"]
            if agree_ratio >= min_agreement:
                clean += 1

        return clean
