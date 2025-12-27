
import pandas as pd
import pickle
import sys
import os

# Adjust the Python path to include the project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from execution.mt5_data_feed import MT5DataFeed
from trading_core.signal_engine import SignalEngine
from trading_core.ml_router import MLRouter
from trading_core.execution_flags import ExecutionFlags, MLMode
from config.allowed_symbols import ALLOWED_SYMBOLS
from config.settings import TIMEFRAME_BARS, ML_MODEL_PATH
from monitoring.logger import logger

def train_and_save_model():
    """
    Trains a machine learning model on historical data for all allowed symbols
    and saves it to a file.
    """
    logger.info("🚀 Starting offline model training process...")

    # Initialize components
    feed = MT5DataFeed()
    signal_engine = SignalEngine(confidence_threshold=0.7)

    # Set up execution flags for training mode
    execution_flags = ExecutionFlags(ml_mode=MLMode.TRAINING)
    ml_router = MLRouter(execution_flags)

    all_features = []
    all_dfs = []

    # Fetch data and prepare features for each symbol
    for symbol in ALLOWED_SYMBOLS:
        logger.info(f"Fetching data for {symbol}...")
        df = feed.get_candles(symbol, TIMEFRAME_BARS, count=5000)  # Fetch more data for training
        if df is None or df.empty or len(df) < 100:
            logger.warning(f"Insufficient data for {symbol}, skipping.")
            continue

        features = signal_engine.prepare_features(df)
        all_features.append(features)
        all_dfs.append(df)

    if not all_features:
        logger.error("No data available for training. Exiting.")
        feed.shutdown()
        return

    # Combine data from all symbols
    combined_features = pd.concat(all_features, ignore_index=True)
    combined_df = pd.concat(all_dfs, ignore_index=True)

    # Train the model
    logger.info("Training the ML model...")
    ml_router.update_model(combined_features, combined_df)

    # Save the trained model
    try:
        with open(ML_MODEL_PATH, "wb") as model_file:
            pickle.dump(ml_router.model, model_file)
        logger.success(f"✅ Model saved successfully to {ML_MODEL_PATH}")
    except Exception as e:
        logger.error(f"❌ Failed to save the model: {e}")

    # Shutdown MT5 connection
    feed.shutdown()

if __name__ == "__main__":
    train_and_save_model()
