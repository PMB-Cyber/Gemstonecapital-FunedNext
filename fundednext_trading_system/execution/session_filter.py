from datetime import datetime, time as dt_time
from fundednext_trading_system.monitoring.logger import logger


class SessionFilter:
    """
    Controls when trading is allowed based on market sessions (UTC).
    """

    LONDON_SESSION = (dt_time(7, 0), dt_time(11, 0))
    NY_SESSION = (dt_time(13, 0), dt_time(17, 0))

    def __init__(self, allow_london=True, allow_ny=True):
        self.allow_london = allow_london
        self.allow_ny = allow_ny

    def _in_range(self, now, start, end):
        return start <= now <= end

    def is_trading_allowed(self) -> bool:
        now_utc = datetime.utcnow().time()

        in_london = self._in_range(
            now_utc, *self.LONDON_SESSION
        )
        in_ny = self._in_range(
            now_utc, *self.NY_SESSION
        )

        if (self.allow_london and in_london) or (
            self.allow_ny and in_ny
        ):
            return True

        logger.info(
            f"⏳ Session Filter active — outside trading hours (UTC {now_utc})"
        )
        return False
