import subprocess
import sys
import os
from fundednext_trading_system.monitoring.logger import logger

class RetrainingManager:
    def __init__(self):
        self.retraining_processes = {}

    def trigger_retraining(self, symbol):
        """
        Triggers the retraining script for a given symbol in a separate process.
        """
        if symbol in self.retraining_processes and self.retraining_processes[symbol].poll() is None:
            logger.warning(f"Retraining for {symbol} is already in progress.")
            return

        logger.info(f"Triggering retraining for {symbol}.")
        script_path = os.path.join(os.path.dirname(__file__), "retrain_model.py")
        process = subprocess.Popen([sys.executable, script_path, symbol])
        self.retraining_processes[symbol] = process
