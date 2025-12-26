import requests
import os
import logging
from datetime import datetime

PRIMARY_WEBHOOK = "https://discordapp.com/api/webhooks/1406710987654037534/Linn2RlPN9BwdVOyWWMJlpz0llYWWKynPTpAZyBzDIqFu9qrsMwYffvllOlVj3IG_oRk"
SECONDARY_WEBHOOK = "https://discordapp.com/api/webhooks/1452230424729489500/P8JoavtGItQR0OFk3k-mymSd8sbY2FKm-T16dpDOexfp-EcZXEjKwqjnaNAIEF92TjC-"
WEBHOOKS = [PRIMARY_WEBHOOK, SECONDARY_WEBHOOK]

# Set up local logging for better diagnostics
logger = logging.getLogger("discord_logger")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

def broadcast(message: str):
    """
    Broadcasts a message to all defined Discord webhooks.
    Adds retries and error logging.
    """
    payload = {"content": message}
    for hook in WEBHOOKS:
        if hook:
            try:
                response = requests.post(hook, json=payload, timeout=5)
                if response.status_code != 204:  # HTTP 204 No Content means success
                    logger.error(f"Failed to send message to {hook}. HTTP Status: {response.status_code}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Error sending message to {hook}: {e}")

def send_discord_update(stats: dict):
    """
    Send a detailed system update with stats to Discord.
    Uses embeds for better formatting.
    """
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    embed = {
        "embeds": [
            {
                "title": "Trading System Status Update",
                "description": f"**Timestamp:** {timestamp}",
                "fields": [
                    {"name": "Total Trades", "value": str(stats.get('trades', 0)), "inline": True},
                    {"name": "Open Positions", "value": str(stats.get('open_positions', 0)), "inline": True},
                    {"name": "Total PnL", "value": f"${stats.get('pnl', 0.0):.2f}", "inline": True},
                    {"name": "Regime", "value": stats.get('regime', 'N/A'), "inline": True},
                    {"name": "Active Symbols", "value": ", ".join(stats.get('active_symbols', [])), "inline": False},
                ],
                "color": 3066993  # Green color
            }
        ]
    }

    for hook in WEBHOOKS:
        if hook:
            try:
                response = requests.post(hook, json=embed, timeout=5)
                if response.status_code != 204:
                    logger.error(f"Failed to send embed to {hook}. HTTP Status: {response.status_code}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Error sending embed to {hook}: {e}")

