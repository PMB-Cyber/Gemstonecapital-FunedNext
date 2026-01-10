"""
WEBHOOK KILL SWITCH (CURRENTLY BYPASSED)

This module is intentionally DISABLED for:
- go_live_validation
- trial trading
- early funded evaluation

To enable later:
- Set ENABLE_WEBHOOK_KILL=true
- Set WEBHOOK_KILL_SECRET
"""

import os
import threading
from fundednext_trading_system.monitoring.logger import logger

# =========================
# CONFIG
# =========================
WEBHOOK_ENABLED = os.getenv("ENABLE_WEBHOOK_KILL", "false").lower() == "true"
WEBHOOK_SECRET = os.getenv("WEBHOOK_KILL_SECRET")

KILL_SWITCH_ACTIVE = False


# =========================
# START SERVER (DISABLED)
# =========================
def start_webhook_server(*args, **kwargs):
    if not WEBHOOK_ENABLED:
        logger.warning("🚫 Webhook kill switch BYPASSED (disabled)")
        return

    # Lazy import only if enabled
    from flask import Flask, request, jsonify

    app = Flask(__name__)

    def _authorized(req):
        secret = req.headers.get("X-KILL-SECRET")
        return secret == WEBHOOK_SECRET

    @app.route("/kill-switch/ON", methods=["POST"])
    def activate():
        global KILL_SWITCH_ACTIVE
        if not _authorized(request):
            return jsonify({"error": "unauthorized"}), 403
        KILL_SWITCH_ACTIVE = True
        logger.critical("🚨 WEBHOOK KILL SWITCH ACTIVATED")
        return jsonify({"status": "ON"}), 200

    @app.route("/kill-switch/OFF", methods=["POST"])
    def deactivate():
        global KILL_SWITCH_ACTIVE
        if not _authorized(request):
            return jsonify({"error": "unauthorized"}), 403
        KILL_SWITCH_ACTIVE = False
        logger.warning("🟢 WEBHOOK KILL SWITCH DEACTIVATED")
        return jsonify({"status": "OFF"}), 200

    def run():
        app.run(host="0.0.0.0", port=9000)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    logger.info("🌐 Webhook kill switch server started")


# =========================
# PUBLIC CHECK (SAFE)
# =========================
def check_webhook_kill_switch() -> bool:
    if not WEBHOOK_ENABLED:
        return False
    return KILL_SWITCH_ACTIVE
