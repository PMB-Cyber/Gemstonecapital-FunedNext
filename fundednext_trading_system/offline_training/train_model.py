
import pandas as pd
import pickle
import sys
import os
import numpy as np

from execution.mt5_data_feed import MT5DataFeed
from trading_core.signal_engine import SignalEngine
from trading_core.ml_router import MLRouter
from trading_core.execution_flags import ExecutionFlags, MLMode, AccountPhase, ExecutionMode
from config.settings import TIMEFRAME_BARS, MODELS_DIR, ALLOWED_SYMBOLS
from monitoring.logger import logger
from offline_training.offline_training import MonteCarloValidator

def run_backtest(model, features, df):
    """
    Runs a simple backtest and returns a list of trade returns.
    """
    logger.info("Running backtest on hold-out data...")
    trade_returns = []

    # Align features index with df index
    features, df = features.align(df, join='inner', axis=0)

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
    Trains a machine learning model for each symbol, validates it using Monte Carlo simulation,
    and saves it if validation passes.
    """
    logger.info("🚀 Starting offline model training process for each symbol...")

    feed = MT5DataFeed()
    signal_engine = SignalEngine(confidence_threshold=0.7)
    execution_flags = ExecutionFlags(
        account_phase=AccountPhase.CHALLENGE,
        execution_mode=ExecutionMode.SHADOW,
        ml_mode=MLMode.TRAINING
    )
    validator = MonteCarloValidator()

    # Create models directory if it doesn't exist
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)
        logger.info(f"Created directory: {MODELS_DIR}")

    for symbol in ALLOWED_SYMBOLS:
        logger.info(f"===== Processing symbol: {symbol} =====")
        logger.info(f"Fetching data for {symbol}...")
        df = feed.get_candles(symbol, TIMEFRAME_BARS, count=5000)
        if df is None or df.empty or len(df) < 200:
            logger.warning(f"Insufficient data for {symbol}, skipping.")
            continue

        features = signal_engine.prepare_features(df)

        # Align dataframes to ensure features and target are correctly matched
        features, df = features.align(df, join='inner', axis=0)

        # Split data into training and validation sets (80/20 split)
        split_index = int(len(df) * 0.8)

        train_df = df.iloc[:split_index]
        val_df = df.iloc[split_index:]

        train_features = features.iloc[:split_index]
        val_features = features.iloc[split_index:]

        logger.info(f"Training on {len(train_df)} data points, validating on {len(val_df)}.")

        ml_router = MLRouter(execution_flags) # Re-instantiate for a fresh model

        logger.info(f"Training the ML model for {symbol}...")
        ml_router.update_model(train_features, train_df)

        # Run backtest and Monte Carlo validation
        trade_returns = run_backtest(ml_router.model, val_features, val_df)
        if not trade_returns:
            logger.error(f"No trades were generated during backtest for {symbol}. Cannot validate.")
            continue # Move to the next symbol

        report = validator.run(trade_returns)
        logger.info(f"📊 MONTE CARLO VALIDATION RESULT for {symbol}")
        for k, v in report.items():
            logger.info(f"{k}: {v}")

        if not report["passed"]:
            logger.error(f"❌ Model for {symbol} failed Monte Carlo validation. Not saving the model.")
            continue # Move to the next symbol

        logger.success(f"✅ Model for {symbol} passed Monte Carlo validation.")

        # Save the trained model
        model_path = os.path.join(MODELS_DIR, f"model_{symbol}.pkl")
        try:
            with open(model_path, "wb") as model_file:
                pickle.dump(ml_router.model, model_file)
            logger.success(f"✅ Model for {symbol} saved successfully to {model_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save the model for {symbol}: {e}")

    feed.shutdown()
    logger.info("✅ Completed training process for all symbols.")

if __name__ == "__main__":
    train_and_save_model()
