
import os
import pickle
from loguru import logger
import sys

# Adjust the Python path to include the project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.settings import MODELS_DIR

def load_model_for_symbol(symbol: str):
    """
    Loads a pre-trained model for a specific symbol.
    """
    model_path = os.path.join(MODELS_DIR, f"model_{symbol}.pkl")

    if not os.path.exists(model_path):
        logger.warning(f"No trained model found for {symbol} at {model_path}. ML inference will be skipped.")
        return None

    try:
        with open(model_path, "rb") as model_file:
            model = pickle.load(model_file)
        logger.info(f"Successfully loaded model for {symbol} from {model_path}.")
        return model
    except Exception as e:
        logger.error(f"Failed to load the model for {symbol} from {model_path}: {e}")
        return None
