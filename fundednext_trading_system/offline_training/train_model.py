
import pandas as pd
import pickle
import sys
import os
import numpy as np

# Adjust the Python path to include the project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from execution.mt5_data_feed import MT5DataFeed
from trading_core.signal_engine import SignalEngine
from trading_core.ml_router import MLRouter
from trading_core.execution_flags import ExecutionFlags, MLMode
from config.allowed_symbols import ALLOWED_SYMBOLS
from config.settings import TIMEFRAME_BARS, ML_MODEL_PATH
from monitoring.logger import logger
from offline_training.offline_training import MonteCarloValidator

def run_backtest(model, features, df):
    """
    Runs a simple backtest and returns a list of trade returns.
    """
    logger.info("Running backtest on hold-out data...")
    trade_returns = []

    # Ensure the DataFrame index is a DatetimeIndex if it's not already
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # Align features index with df index
    features.index = df.index[:len(features)]

    for i in range(1, len(features)):
        # Ensure we don't go out of bounds for the target
        if i >= len(df) -1:
            break

        current_features = features.iloc[i:i+1]

        try:
            # Predict using the model
            pred_proba = model.predict_proba(current_features.values)
            side = "buy" if pred_proba[0][1] > pred_proba[0][0] else "sell"

            # Calculate return for the next candle
            price_change = df['close'].iloc[i+1] - df['close'].iloc[i]

            if side == "buy":
                trade_returns.append(price_change / df['close'].iloc[i])
            else: # sell
                trade_returns.append(-price_change / df['close'].iloc[i])
        except Exception as e:
            logger.warning(f"Could not make prediction at step {i}: {e}")
            continue

    logger.success(f"Backtest complete. Generated {len(trade_returns)} trade returns.")
    return trade_returns


def train_and_save_model():
    """
    Trains a machine learning model, validates it using Monte Carlo simulation,
    and saves it if validation passes.
    """
    logger.info("🚀 Starting offline model training process...")

    feed = MT5DataFeed()
    signal_engine = SignalEngine(confidence_threshold=0.7)
    execution_flags = ExecutionFlags(ml_mode=MLMode.TRAINING)
    ml_router = MLRouter(execution_flags)
    validator = MonteCarloValidator()

    all_features = []
    all_dfs = []

    for symbol in ALLOWED_SYMBOLS:
        logger.info(f"Fetching data for {symbol}...")
        df = feed.get_candles(symbol, TIMEFRAME_BARS, count=5000)
        if df is None or df.empty or len(df) < 200:
            logger.warning(f"Insufficient data for {symbol}, skipping.")
            continue

        features = signal_engine.prepare_features(df)
        all_features.append(features)
        all_dfs.append(df)

    if not all_features:
        logger.error("No data available for training. Exiting.")
        feed.shutdown()
        return

    combined_features = pd.concat(all_features, ignore_index=True)
    combined_df = pd.concat(all_dfs, ignore_index=True)

    # Split data into training and validation sets (80/20 split)
    split_index = int(len(combined_df) * 0.8)

    train_df = combined_df.iloc[:split_index]
    val_df = combined_df.iloc[split_index:]

    train_features = combined_features.iloc[:split_index]
    val_features = combined_features.iloc[split_index:]

    logger.info(f"Training on {len(train_df)} data points, validating on {len(val_df)}.")

    # Train the model
    logger.info("Training the ML model...")
    ml_router.update_model(train_features, train_df)

    # Run backtest and Monte Carlo validation
    trade_returns = run_backtest(ml_router.model, val_features, val_df)
    if not trade_returns:
        logger.error("No trades were generated during backtest. Cannot validate.")
        feed.shutdown()
        return

    report = validator.run(trade_returns)
    logger.info("📊 MONTE CARLO VALIDATION RESULT")
    for k, v in report.items():
        logger.info(f"{k}: {v}")

    if not report["passed"]:
        logger.error("❌ Model failed Monte Carlo validation. Not saving the model.")
        feed.shutdown()
        return

    logger.success("✅ Model passed Monte Carlo validation.")

    # Save the trained model
    try:
        with open(ML_MODEL_PATH, "wb") as model_file:
            pickle.dump(ml_router.model, model_file)
        logger.success(f"✅ Model saved successfully to {ML_MODEL_PATH}")
    except Exception as e:
        logger.error(f"❌ Failed to save the model: {e}")

    feed.shutdown()

if __name__ == "__main__":
    train_and_save_model()
