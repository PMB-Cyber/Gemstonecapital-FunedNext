import json
import os
from fundednext_trading_system.monitoring.logger import logger

LOCK_FILE = "state/challenge_lock.json"


def is_challenge_locked() -> bool:
    if not os.path.exists(LOCK_FILE):
        return False

    with open(LOCK_FILE, "r") as f:
        return json.load(f).get("locked", False)


def lock_challenge():
    os.makedirs("state", exist_ok=True)

    with open(LOCK_FILE, "w") as f:
        json.dump(
            {
                "locked": True,
            },
            f,
            indent=2,
        )

    logger.critical("🔒 CHALLENGE MODE LOCKED — FUNDED ONLY")
