"""
heartbeat.py

Live heartbeat logger for FundedNext trading system.
Displays live:
- Open positions
- Partial TP progress
- Trailing SL levels
- ML predictions / confidence
- Equity and risk status
"""

import time
import os
from monitoring.logger import logger
from config.allowed_symbols import ALLOWED_SYMBOLS

def clear_console():
    """Clear the console for live dashboard effect."""
    os.system("cls" if os.name == "nt" else "clear")


def print_status(
    risk_manager,
    execution_flags,
    feed,
    partial_tp_manager,
    trailing_sl_manager,
    ml_router,
    symbol_stats=None,   # <-- ADD THIS
    refresh_seconds=15,
):

    """
    Continuously prints live status of the system in the console.
    Loops until interrupted.
    """
    try:
        while True:
            clear_console()
            print("💓 FUNDAMENTAL HEARTBEAT | Live Trading Dashboard\n")

            header = f"{'SYMBOL':<10} | {'POSITIONS':<10} | {'PARTIAL_TP':<20} | {'TRAIL_SL':<10} | {'ML_STATUS':<15}"
            print(header)
            print("-" * len(header))

            for symbol in ALLOWED_SYMBOLS:
                # Open positions
                try:
                    positions = feed.get_positions(symbol) if feed else []
                    positions_count = len(positions)
                except Exception:
                    positions_count = "ERR"

                # Partial TP
                try:
                    tp_status = partial_tp_manager.status(symbol) if partial_tp_manager else "-"
                except Exception:
                    tp_status = "ERR"

                # Trailing SL
                try:
                    sl_level = trailing_sl_manager.current_sl(symbol) if trailing_sl_manager else "-"
                except Exception:
                    sl_level = "ERR"

                # ML status
                try:
                    last_signal = ml_router.last_signal(symbol) if ml_router else None
                    if last_signal:
                        side, score = last_signal
                        ml_status = f"{side.upper()} ({score:.2f})"
                    else:
                        ml_status = "-"
                except Exception:
                    ml_status = "ERR"

                # Print row
                row = f"{symbol:<10} | {positions_count:<10} | {str(tp_status):<20} | {sl_level:<10} | {ml_status:<15}"
                print(row)

            # Equity / Risk
            try:
                balance = risk_manager.current_balance()
                daily_loss = risk_manager.daily_loss
                print(f"\n💰 Balance: {balance:.2f} | Daily Loss: {daily_loss:.2f}")
            except Exception as e:
                print(f"⚠️ Failed to fetch balance/risk info: {e}")

            print(f"\n⏱️ Refreshing every {refresh_seconds} seconds...")
            time.sleep(refresh_seconds)

    except KeyboardInterrupt:
        print("\n🛑 Heartbeat monitoring stopped manually.")


# Optional: for threaded integration in master orchestrator
def start_heartbeat_thread(risk_manager, execution_flags, feed, partial_tp_manager, trailing_sl_manager, ml_router):
    import threading
    heartbeat_thread = threading.Thread(
        target=print_status,
        args=(risk_manager, execution_flags, feed, partial_tp_manager, trailing_sl_manager, ml_router),
        daemon=True,  # Ensures it stops when main thread exits
    )
    heartbeat_thread.start()
    return heartbeat_thread
