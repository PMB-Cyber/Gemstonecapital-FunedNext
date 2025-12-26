import os
import json
from monitoring.logger import logger

# =========================
# CONFIG
# =========================
STATE_FILE = "models/active/model_state.json"

MODEL_FREEZE = os.getenv("MODEL_FREEZE", "true").lower() == "true"

# This should ONLY change after manual approval
ACTIVE_MODEL_VERSION = "v1.0.0-FROZEN"


# =========================
# MODEL PROMOTION / ROLLBACK STATE
# =========================
def promote_model_version(symbol: str, model_path: str):
    """
    Promote a new model to active and store previous version
    for rollback safety.
    """
    os.makedirs("models/active", exist_ok=True)

    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
    else:
        state = {}

    previous = state.get(symbol, {}).get("current")

    state[symbol] = {
        "current": model_path,
        "previous": previous,
    }

    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

    logger.info(
        f"📌 Model promoted | {symbol} | current={model_path}"
    )


def get_model_state(symbol: str) -> dict:
    if not os.path.exists(STATE_FILE):
        return {}

    with open(STATE_FILE, "r") as f:
        state = json.load(f)

    return state.get(symbol, {})


# =========================
# ML FREEZE GUARD
# =========================
def assert_model_frozen(requested_version: str):
    """
    Prevent loading any model that is not the approved frozen version.
    """
    if MODEL_FREEZE and requested_version != ACTIVE_MODEL_VERSION:
        raise RuntimeError(
            f"🔒 MODEL FREEZE ACTIVE — Attempted load: {requested_version}"
        )


def get_active_model_version():
    """
    Returns the approved frozen model version.
    """
    return ACTIVE_MODEL_VERSION
