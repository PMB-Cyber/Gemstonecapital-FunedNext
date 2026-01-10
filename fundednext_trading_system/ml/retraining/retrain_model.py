
import os
import sys
import pickle
import pandas as pd
from sklearn.model_selection import train_test_split

from fundednext_trading_system.execution.mt5_data_feed import MT5DataFeed
from fundednext_trading_system.trading_core.signal_engine import SignalEngine
from fundednext_trading_system.config.settings import TIMEFRAME_BARS, MODELS_DIR, MODEL_VERSION
from fundednext_trading_system.monitoring.logger import logger
from fundednext_trading_system.offline_training.offline_training import MonteCarloValidator
from fundednext_trading_system.offline_training.train_model import run_backtest

def retrain_model_for_symbol(symbol: str, new_data_window: int = 500):
    """
    Retrains the model for a specific symbol with new data, using a proper
    train/validation split to prevent data leakage.
    """
    logger.info(f"🚀 Starting incremental retraining for {symbol}...")

    feed = MT5DataFeed()
    signal_engine = SignalEngine()
    validator = MonteCarloValidator()

    # Define model path
    model_path = os.path.join(MODELS_DIR, f"model_{symbol}_{MODEL_VERSION}.pkl")

    # 1. Load existing model
    if not os.path.exists(model_path):
        logger.error(f"Cannot retrain: No existing model found for {symbol} at {model_path}.")
        feed.shutdown()
        return

    try:
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        logger.info(f"Loaded existing model for {symbol}.")
    except Exception as e:
        logger.error(f"Failed to load model for {symbol}: {e}")
        feed.shutdown()
        return

    # 2. Fetch new and historical data
    logger.info(f"Fetching last {new_data_window} candles for {symbol}...")
    new_df = feed.get_candles(symbol, TIMEFRAME_BARS, count=new_data_window)
    if new_df is None or new_df.empty or len(new_df) < 50:
        logger.warning(f"Insufficient new data for {symbol}, skipping retraining.")
        feed.shutdown()
        return

    logger.info("Fetching historical data for combined dataset...")
    historical_df = feed.get_candles(symbol, TIMEFRAME_BARS, count=4500)

    # 3. Combine and prepare the full dataset
    combined_df = pd.concat([historical_df, new_df]).drop_duplicates().sort_index()
    if len(combined_df) < 200:
        logger.warning(f"Insufficient total data for {symbol} after combining, skipping.")
        feed.shutdown()
        return

    features = signal_engine.prepare_features(combined_df)

    # Align dataframes to ensure features and target are correctly matched
    features, combined_df = features.align(combined_df, join='inner', axis=0)

    # 4. Create a proper train/validation split
    split_index = int(len(combined_df) * 0.8)

    train_df = combined_df.iloc[:split_index]
    val_df = combined_df.iloc[split_index:]

    train_features = features.iloc[:split_index]
    val_features = features.iloc[split_index:]

    logger.info(f"Retraining on {len(train_df)} data points, validating on {len(val_df)}.")

    # 5. Retrain the model on the new training set
    try:
        model.fit(train_features.values, train_df['target'].values) # Assuming 'target' is the column to predict
        logger.success(f"Successfully retrained model for {symbol}.")
    except Exception as e:
        logger.error(f"An error occurred during model fitting for {symbol}: {e}")
        feed.shutdown()
        return

    # 6. Validate the retrained model on the unseen validation set
    logger.info(f"Validating retrained model for {symbol} on unseen data...")
    trade_returns = run_backtest(model, val_features, val_df)
    if not trade_returns:
        logger.error(f"No trades were generated during backtest for {symbol}. Cannot validate.")
        feed.shutdown()
        return

    report = validator.run(trade_returns)
    logger.info(f"📊 MONTE CARLO VALIDATION RESULT for {symbol}")
    for k, v in report.items():
        logger.info(f"{k}: {v}")

    if not report["passed"]:
        logger.error(f"❌ Retrained model for {symbol} failed Monte Carlo validation on unseen data. Not saving.")
        feed.shutdown()
        return

    logger.success(f"✅ Retrained model for {symbol} passed Monte Carlo validation.")

    # 7. Save the updated model
    try:
        with open(model_path, "wb") as f:
            pickle.dump(model, f)
        logger.success(f"✅ Successfully saved retrained model for {symbol} to {model_path}")
    except Exception as e:
        logger.error(f"Failed to save the retrained model for {symbol}: {e}")

    feed.shutdown()

if __name__ == "__main__":
    # Example usage:
    if len(sys.argv) > 1:
        symbol_to_retrain = sys.argv[1].upper()
        retrain_model_for_symbol(symbol_to_retrain)
    else:
        print("Usage: python retrain_model.py <SYMBOL>")
        # Example: python fundednext_trading_system/ml/retraining/retrain_model.py EURUSD
