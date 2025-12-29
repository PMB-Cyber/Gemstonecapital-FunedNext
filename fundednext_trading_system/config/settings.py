# =========================================================
# GENERAL
# =========================================================
import os

ENVIRONMENT = os.getenv("ENVIRONMENT", "production").lower()
TIMEFRAME_BARS = 300
LOOP_SLEEP_SECONDS = 60
PER_SYMBOL_THROTTLE = 0.3

# =========================================================
# SYMBOLS
# =========================================================
ALLOWED_SYMBOLS = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "XAUUSD",
    "US30",
    "NDX100",
]

# =========================================================
# ATR SETTINGS
# =========================================================
ATR_PERIOD = 14
ATR_SL_MULTIPLIER = 1.2
ATR_TP_MULTIPLIERS = (1.0, 2.0)
TP_CLOSE_PERCENTS = (0.3, 0.3)

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
        "ACCOUNT_BALANCE": 10_000,
        "DAILY_LOSS_LIMIT": 500,        # 5%
        "MAX_LOSS_LIMIT": 1_000,        # 10%
        "MAX_RISK_PER_TRADE": 100,      # 1%
        "PROFIT_TARGET": 800,           # 8%
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

# =========================================================
# FILE PATHS
# =========================================================
MODELS_DIR = "fundednext_trading_system/models/"
STATS_PATH = "stats.pkl"
