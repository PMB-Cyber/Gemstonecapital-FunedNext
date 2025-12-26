import MetaTrader5 as mt5
from flask import Flask, jsonify
from trading_core.capital_scaler import CapitalScaler
from config.fundednext_rules import ACCOUNT_BALANCE
from monitoring.logger import logger

app = Flask(__name__)

scaler = CapitalScaler(ACCOUNT_BALANCE)


@app.route("/api/scaling", methods=["GET"])
def scaling_status():
    info = mt5.account_info()
    if not info:
        return jsonify({"error": "MT5 not connected"}), 500

    equity = info.equity
    multiplier = scaler.get_multiplier()
    drawdown = scaler.in_drawdown()

    return jsonify({
        "account_balance": ACCOUNT_BALANCE,
        "current_equity": round(equity, 2),
        "scaling_multiplier": round(multiplier, 2),
        "drawdown_active": drawdown,
        "risk_mode": "FROZEN" if drawdown else "SCALING",
    })


def start_dashboard(host="127.0.0.1", port=5050):
    logger.info(f"📊 Scaling dashboard running on http://{host}:{port}")
    app.run(host=host, port=port)
