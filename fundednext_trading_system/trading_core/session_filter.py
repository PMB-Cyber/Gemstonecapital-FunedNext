from datetime import datetime
from fundednext_trading_system.config.settings import SESSION_TIMES, SYMBOL_SESSIONS
from fundednext_trading_system.monitoring.logger import logger

class SessionFilter:
    def __init__(self):
        self.session_times = {
            session: (
                datetime.strptime(start, '%H:%M').time(),
                datetime.strptime(end, '%H:%M').time()
            )
            for session, (start, end) in SESSION_TIMES.items()
        }

    def is_in_session(self, symbol):
        """
        Checks if a symbol is within its allowed trading session.
        """
        now = datetime.utcnow().time()
        allowed_sessions = SYMBOL_SESSIONS.get(symbol, [])

        if not allowed_sessions:
            logger.warning(f"No session information for symbol: {symbol}. Allowing trade.")
            return True

        for session in allowed_sessions:
            start_time, end_time = self.session_times.get(session, (None, None))
            if start_time and end_time:
                if start_time <= now <= end_time:
                    logger.info(f"Symbol {symbol} is within the {session} session.")
                    return True

        logger.warning(f"Symbol {symbol} is outside of its allowed trading sessions.")
        return False
