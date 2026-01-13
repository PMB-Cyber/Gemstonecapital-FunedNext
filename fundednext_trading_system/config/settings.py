# =========================================================
# GENERAL
# =========================================================
import os

ENVIRONMENT = os.getenv("ENVIRONMENT", "production").lower()
TIMEFRAME_BARS = 86400  # 24 hours
LOOP_SLEEP_SECONDS = 60
PER_SYMBOL_THROTTLE = 0.3

# =========================================================
# SYMBOLS
# =========================================================
ALLOWED_SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "US30", "NDX100",
    "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "CADJPY", "CHFJPY",
    "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY", "GBPAUD",
    "GBPJPY", "NZDUSD", "USDCAD", "USDCHF", "GER30", "UK100",
    "SPX500", "XAGUSD"
]

# =========================================================
# SYMBOL-SPECIFIC PARAMETERS
# =========================================================
SYMBOL_PARAMS = {
    "DEFAULT": {
        "ATR_PERIOD": 14,
        "ATR_SL_MULTIPLIER": 1.2,
        "ATR_TP_MULTIPLIERS": (1.0, 2.0),
        "TP_CLOSE_PERCENTS": (0.3, 0.3),
    },
    "XAUUSD": {
        "ATR_PERIOD": 20,
        "ATR_SL_MULTIPLIER": 1.5,
    },
    "NDX100": {
        "ATR_PERIOD": 10,
        "ATR_SL_MULTIPLIER": 1.0,
    },
    "SPX500": {
        "ATR_PERIOD": 10,
        "ATR_SL_MULTIPLIER": 1.0,
    },
    "GER30": {
        "ATR_PERIOD": 10,
        "ATR_SL_MULTIPLIER": 1.0,
    },
    "UK100": {
        "ATR_PERIOD": 10,
        "ATR_SL_MULTIPLIER": 1.0,
    },
}

# =========================================================
# ACCOUNT & EXECUTION MODES
# =========================================================
# These settings are now derived from the ENVIRONMENT variable.
if ENVIRONMENT == "production":
    DRY_RUN = False
    REPLAY_MODE = False
    ACCOUNT_PHASE = os.getenv("ACCOUNT_PHASE", "CHALLENGE").upper()
    EXECUTION_MODE = "LIVE"
    ML_MODE = "INFERENCE"
else:
    DRY_RUN = True
    REPLAY_MODE = False
    ACCOUNT_PHASE = "CHALLENGE"
    EXECUTION_MODE = "PAPER"
    ML_MODE = "TRAINING"

# =========================================================
# PHASE-SPECIFIC RULES (FundedNext)
# =========================================================
PHASE_RULES = {
    "CHALLENGE": {
        "ACCOUNT_BALANCE": 5_000,
        "DAILY_LOSS_LIMIT": 250,        # 5%
        "MAX_LOSS_LIMIT": 500,        # 10%
        "MAX_RISK_PER_TRADE": 250,      # 1%
        "PROFIT_TARGET": 400,           # 8%
    },
    "FUNDED": {
        "ACCOUNT_BALANCE": 10_000,
        "DAILY_LOSS_LIMIT": 300,        # 3%
        "MAX_LOSS_LIMIT": 600,          # 6%
        "MAX_RISK_PER_TRADE": 50,       # 0.5%
        "WITHDRAWAL_BUFFER": 200,
    }
}

# Select the current rules based on ACCOUNT_PHASE
CURRENT_RULES = PHASE_RULES[ACCOUNT_PHASE]

def get_challenge_optimized_params():
    """
    Returns a set of optimized parameters for the 5k challenge.
    """
    return {
        "ATR_PERIOD": 10,
        "ATR_SL_MULTIPLIER": 1.0,
        "ATR_TP_MULTIPLIERS": (1.5, 2.5),
        "TP_CLOSE_PERCENTS": (0.4, 0.4),
    }

# =========================================================
# FILE PATHS
# =========================================================
MODELS_DIR = "fundednext_trading_system/models/"
STATS_PATH = "stats.pkl"

# =========================================================
# RISK MANAGEMENT
# =========================================================
CORRELATION_THRESHOLD = 0.8

# =========================================================
# SESSION FILTERING
# =========================================================
SESSION_TIMES = {
    "TOKYO": ("00:00", "09:00"),
    "LONDON": ("08:00", "17:00"),
    "NEW_YORK": ("13:00", "22:00"),
}

SYMBOL_SESSIONS = {
    "EURUSD": ["LONDON", "NEW_YORK"],
    "GBPUSD": ["LONDON", "NEW_YORK"],
    "USDJPY": ["TOKYO", "NEW_YORK"],
    "XAUUSD": ["LONDON", "NEW_YORK"],
    "US30": ["NEW_YORK"],
    "NDX100": ["NEW_YORK"],
    "AUDCAD": ["TOKYO", "NEW_YORK"],
    "AUDCHF": ["TOKYO", "LONDON"],
    "AUDJPY": ["TOKYO"],
    "AUDNZD": ["TOKYO"],
    "CADJPY": ["TOKYO", "NEW_YORK"],
    "CHFJPY": ["TOKYO", "LONDON"],
    "EURAUD": ["LONDON", "TOKYO"],
    "EURCAD": ["LONDON", "NEW_YORK"],
    "EURCHF": ["LONDON"],
    "EURGBP": ["LONDON"],
    "EURJPY": ["LONDON", "TOKYO"],
    "GBPAUD": ["LONDON", "TOKYO"],
    "GBPJPY": ["LONDON", "TOKYO"],
    "NZDUSD": ["TOKYO", "NEW_YORK"],
    "USDCAD": ["NEW_YORK"],
    "USDCHF": ["LONDON", "NEW_YORK"],
    "GER30": ["LONDON"],
    "UK100": ["LONDON"],
    "SPX500": ["NEW_YORK"],
    "XAGUSD": ["LONDON", "NEW_YORK"],
}
