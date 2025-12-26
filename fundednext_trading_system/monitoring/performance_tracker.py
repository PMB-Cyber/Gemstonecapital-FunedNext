from monitoring.metrics import (
    signal_count,
    buy_count,
    sell_count,
    confidence_scores
)
from loguru import logger

def record_signal(symbol, side, score):
    signal_count[symbol] += 1
    confidence_scores[symbol].append(score)

    if side == "buy":
        buy_count[symbol] += 1
    elif side == "sell":
        sell_count[symbol] += 1

def print_stats():
    logger.info("📊 LIVE PERFORMANCE SUMMARY")
    for symbol in signal_count:
        avg_conf = sum(confidence_scores[symbol]) / len(confidence_scores[symbol])
        logger.info(
            f"{symbol} | Signals={signal_count[symbol]} "
            f"| Buy={buy_count[symbol]} "
            f"| Sell={sell_count[symbol]} "
            f"| AvgConf={avg_conf:.2f}"
        )
