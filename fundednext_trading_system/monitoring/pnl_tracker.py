from collections import defaultdict
from loguru import logger

symbol_pnl = defaultdict(float)
symbol_trades = defaultdict(int)
symbol_wins = defaultdict(int)
total_pnl = 0.0

def record_trade(trade):
    global total_pnl

    symbol_trades[trade.symbol] += 1
    symbol_pnl[trade.symbol] += trade.pnl
    total_pnl += trade.pnl

    if trade.pnl > 0:
        symbol_wins[trade.symbol] += 1

def print_pnl_summary():
    logger.info("💰 PnL SUMMARY")
    for symbol in symbol_trades:
        win_rate = (
            symbol_wins[symbol] / symbol_trades[symbol]
            if symbol_trades[symbol] else 0
        )
        logger.info(
            f"{symbol} | Trades={symbol_trades[symbol]} "
            f"| PnL={symbol_pnl[symbol]:.2f} "
            f"| WinRate={win_rate:.2%}"
        )

    logger.info(f"TOTAL PnL: {total_pnl:.2f}")
