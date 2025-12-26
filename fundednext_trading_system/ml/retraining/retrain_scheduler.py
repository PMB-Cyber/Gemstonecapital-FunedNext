import os
import sys
import time
from datetime import datetime

from monitoring.logger import logger
from config.allowed_symbols import ALLOWED_SYMBOLS
from ml.retrain_model import retrain

LOCK_FILE = "ml/.retrain.lock"
LOG_FILE = "logs/retrain.log"


# =========================
# LOCKING (CRON SAFE)
# =========================
def acquire_lock():
    if os.path.exists(LOCK_FILE):
        logger.warning("🔒 Retrain already running — skipping")
        sys.exit(0)

    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))


def release_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)


# =========================
# MAIN RETRAIN JOB
# =========================
def run_retraining():
    logger.info("🧠 Starting automated retraining cycle")

    for symbol in ALLOWED_SYMBOLS:
        try:
            logger.info(f"🔁 Retraining {symbol}")
            report = retrain(symbol)

            logger.success(
                f"✅ {symbol} retrained | "
                f"Sharpe={report['sharpe_ratio']} | "
                f"RoR={report['risk_of_ruin']}"
            )

        except Exception as e:
            logger.exception(f"❌ Retraining failed for {symbol}: {e}")

    logger.info("🏁 Retraining cycle completed")


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    try:
        acquire_lock()
        run_retraining()
    finally:
        release_lock()
