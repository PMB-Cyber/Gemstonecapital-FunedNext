# =========================================================
# GENERAL
# =========================================================
ENVIRONMENT = "development"  # "development" or "production"
TIMEFRAME_BARS = 300
LOOP_SLEEP_SECONDS = 60
PER_SYMBOL_THROTTLE = 0.3

# =========================================================
# ATR SETTINGS
# =========================================================
ATR_PERIOD = 14
ATR_SL_MULTIPLIER = 1.2
ATR_TP_MULTIPLIERS = (1.0, 2.0)
TP_CLOSE_PERCENTS = (0.3, 0.3)

# =========================================================
# EXECUTION MODES
# =========================================================
if ENVIRONMENT == "production":
    DRY_RUN = False
    REPLAY_MODE = False
    ACCOUNT_PHASE = "CHALLENGE"
    EXECUTION_MODE = "LIVE"
    ML_MODE = "INFERENCE"
else:
    DRY_RUN = True
    REPLAY_MODE = False
    ACCOUNT_PHASE = "CHALLENGE"
    EXECUTION_MODE = "PAPER"
    ML_MODE = "TRAINING"

# =========================================================
# FILE PATHS
# =========================================================
MODEL_VERSION = "v1.0"
ML_MODEL_PATH = f"model_{MODEL_VERSION}.pkl"
STATS_PATH = "stats.pkl"
