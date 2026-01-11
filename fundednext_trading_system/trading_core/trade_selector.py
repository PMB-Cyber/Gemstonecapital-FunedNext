from typing import List, Dict, Tuple
from fundednext_trading_system.trading_core.correlation_manager import CorrelationManager
from fundednext_trading_system.config.settings import CORRELATION_THRESHOLD
from fundednext_trading_system.monitoring.logger import logger

class TradeSelector:
    def __init__(self, correlation_manager: CorrelationManager):
        self.correlation_manager = correlation_manager

    def select_best_trades(self, potential_trades: List[Dict]) -> List[Dict]:
        """
        Selects the best trade from each group of correlated symbols.

        Args:
            potential_trades: A list of dictionaries, where each dictionary
                              represents a potential trade and contains at least
                              'symbol' and 'score' keys.

        Returns:
            A list of the selected trades.
        """
        if not self.correlation_manager.matrix_ready:
            logger.warning("Correlation matrix not ready. Skipping trade selection.")
            return potential_trades

        # Sort trades by score in descending order
        sorted_trades = sorted(potential_trades, key=lambda x: x['score'], reverse=True)

        selected_trades = []
        discarded_symbols = set()

        for trade in sorted_trades:
            symbol = trade['symbol']
            if symbol in discarded_symbols:
                continue

            selected_trades.append(trade)
            discarded_symbols.add(symbol)

            # Discard other symbols that are highly correlated with the selected one
            for other_trade in sorted_trades:
                other_symbol = other_trade['symbol']
                if other_symbol not in discarded_symbols:
                    correlation = self.correlation_manager.get_correlation(symbol, other_symbol)
                    if abs(correlation) > CORRELATION_THRESHOLD:
                        logger.info(f"Discarding {other_symbol} due to high correlation ({correlation:.2f}) with {symbol}.")
                        discarded_symbols.add(other_symbol)

        return selected_trades
