# FundedNext Trading System

This is a sophisticated, automated trading system designed to interact with the MetaTrader 5 (MT5) platform. It leverages a combination of machine learning and rule-based strategies to execute trades, manage risk, and monitor performance in real-time.

## Table of Contents

- [Key Features](#key-features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [How to Run the System](#how-to-run-the-system)
  - [1. Initial Model Training](#1-initial-model-training)
  - [2. Go-Live Validation](#2-go-live-validation)
  - [3. Run the Main Orchestrator](#3-run-the-main-orchestrator)
- [System Architecture](#system-architecture)
- [Configuration](#configuration)
- [Environments: Production vs. Development](#environments-production-vs-development)
- [Troubleshooting](#troubleshooting)
- [Monitoring](#monitoring)
- [Change Log](#change-log)

## Key Features

- **Hybrid Trading Logic**: Combines an ML model for signal generation with a rule-based fallback system.
- **Expanded Symbol List**: Trades a diverse portfolio of 26 instruments, including major currency pairs, major indices, and metals.
- **Smart Correlation Filtering**: Proactively selects the highest-probability trade from a group of correlated instruments, preventing less promising trades from blocking better opportunities.
- **Session Filtering**: Smartly manages trades by only allowing them during specific trading sessions (Tokyo, London, New York).
- **Symbol-Specific Models**: Trains and deploys a unique ML model for each trading symbol.
- **Robust Data Handling**: Uses the `dukascopy-python` library to fetch and process historical tick data for model training.
- **Incremental Training**: Automatically retrains models with new live data to adapt to changing market conditions.
- **Automated Execution**: Interfaces directly with MT5 to execute and manage trades.
- **Advanced Risk Management**: Features include dynamic position sizing, trailing stop-losses, equity-based kill switches, and correlation-based trade blocking.
- **News Sentiment Analysis**: Integrates news sentiment into the signal generation process to adjust trade confidence.
- **Real-time Monitoring**: Provides a console-based heartbeat, detailed logging, and Discord integration.
- **Centralized Configuration**: Defaults to a production-ready setup, with support for a development mode via environment variables.

## Getting Started

### Prerequisites

-   Python 3.8+
-   MetaTrader 5 terminal installed and running (for production)
-   Git

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2.  **Install Dependencies:**

    The project uses two different files for dependencies, depending on your environment.

    -   **For Production (Windows):**
        ```bash
        pip install -r fundednext_trading_system/requirements.txt
        ```
        This command installs all the necessary packages for running the system in a live trading environment.

    -   **For Development (macOS/Linux):**
        ```bash
        pip install -r fundednext_trading_system/dev_requirements.txt
        ```
        This command installs all production dependencies, plus a mock `MetaTrader5` library and `pytest` for development.

## How to Run the System

The system now defaults to a **production** environment.

### 1. Initial Model Training

Before you can run the main trading system, you need to train the initial machine learning models. This is done by running the `train_model.py` script.

-   **On Windows (Production):**
    The system will automatically use the real `MetaTrader5` library.
    ```cmd
    python -m fundednext_trading_system.offline_training.train_model
    ```

-   **On macOS/Linux (Development):**
    You **must** explicitly set the `ENVIRONMENT` to `development`.
    ```bash
    ENVIRONMENT=development python -m fundednext_trading_system.offline_training.train_model
    ```

This script will:
- Fetch historical tick data for each trading symbol from Dukascopy.
- Resample the tick data into OHLC candles.
- Train a unique model for each symbol.
- Save the trained models to the `fundednext_trading_system/models/` directory.

### 2. Go-Live Validation

Before running in a live environment, it's crucial to run the pre-flight validation script and consult the `go_live_checklist.md` to ensure all configurations are correct.
```bash
python -m fundednext_trading_system.go_live_validation
```

### 3. Run the Main Orchestrator

Once models are trained, run the main trading system.

-   **Production Example:**
    You can optionally specify the account phase.
    ```bash
    ACCOUNT_PHASE=CHALLENGE python -m fundednext_trading_system.main
    ```

-   **Development Example:**
    ```bash
    ENVIRONMENT=development python -m fundednext_trading_system.main
    ```

## System Architecture

The system is designed with a modular architecture, with each component having a specific responsibility.

-   `main.py`: The main entry point of the application.
-   `config/settings.py`: Contains all the configuration settings for the system.
-   `trading_core/`: The core logic of the trading system.
-   `execution/`: Handles the communication with the MT5 platform.
-   `ml/`: Contains the machine learning models and related scripts.
-   `offline_training/`: Contains the script for training the initial models.
-   `monitoring/`: Provides tools for monitoring the system's performance.

## Advanced Risk Management

### Smart Correlation Filtering
The system uses a sophisticated correlation filter to avoid over-exposure to a single market factor. Instead of naively blocking a trade based on an *existing* open position, the system now:
1.  **Generates all potential trades** for a given trading cycle.
2.  **Identifies groups of correlated symbols** among these potential trades.
3.  **Selects only the single trade with the highest confidence score** from each correlated group.
This ensures that the system always picks the best trade from any group of correlated instruments, preventing a less promising trade from blocking a more promising one.

## News Sentiment Analysis
News headlines are fetched from Yahoo Finance, and their sentiment is analyzed using `TextBlob`. This aggregate sentiment score is used by the `SignalEngine` to adjust the confidence level of trading signals.

## Configuration

The system's behavior is controlled by environment variables.

-   `ENVIRONMENT`: Defaults to `production`. Set to `development` for local testing with a mock MT5 library.
-   `ACCOUNT_PHASE`: Set to `CHALLENGE` or `FUNDED` to load the correct risk management rules.

## Environments: Production vs. Development

The `ENVIRONMENT` variable is the most critical setting. **The system now defaults to `production`.**

-   **`production` (Default)**:
    -   Uses the **real `MetaTrader5` library**.
    -   This mode is **only available on Windows**.
    -   The system will automatically run in this mode unless `ENVIRONMENT` is explicitly set to `development`.

-   **`development`**:
    -   Uses a **mock `MetaTrader5` library` for development on non-Windows machines.
    -   To use this mode, you **must** set the environment variable: `ENVIRONMENT=development`.

## Troubleshooting

-   **`ModuleNotFoundError: No module named 'MetaTrader5'`**: This error will occur if you try to run the system in its default production mode on a non-Windows machine, or if the `MetaTrader5` library is not installed correctly.
-   **Monte Carlo Validation Failures**: If the Monte Carlo validation consistently fails, it may indicate an issue with the trading strategy itself. The validation logic was recently updated to be more robust.

## Monitoring

-   **Console**: The terminal displays a live heartbeat with key performance indicators.
-   **Logs**: Detailed logs are saved to the `logs/` directory.

## Change Log

### Feat: Smart Correlation Filtering
-   **`fundednext_trading_system/trading_core/trade_selector.py`**:
    -   Created a new `TradeSelector` class to select the best trade from each group of correlated symbols.
-   **`fundednext_trading_system/main.py`**:
    -   Refactored the main trading loop to work in three phases: signal generation, trade selection, and trade execution.
-   **`fundednext_trading_system/trading_core/risk_manager.py`**:
    -   Removed the old correlation check to avoid redundancy.
-   **`README.md`**:
    -   Updated documentation to explain the new, smarter correlation filtering logic.

### Feat: Expanded Symbol List and Session Filtering
-   **`fundednext_trading_system/config/settings.py`**:
    -   Expanded the `ALLOWED_SYMBOLS` list to 26 instruments.
    -   Added session times and a symbol-to-session mapping for the new `SessionFilter`.
-   **`fundednext_trading_system/execution/dukascopy_data_feed.py`**:
    -   Updated the `DUKASCOPY_SYMBOL_MAP` to include the new symbols.
-   **`fundednext_trading_system/trading_core/session_filter.py`**:
    -   Created a new `SessionFilter` class to manage trading sessions.
-   **`fundednext_trading_system/trading_core/trade_gatekeeper.py`**:
    -   Integrated the `SessionFilter` to block trades outside of allowed trading sessions.
-   **`fundednext_trading_system/main.py`**:
    -   Instantiated the `SessionFilter` and passed it to the `TradeGatekeeper`.
-   **`README.md`**:
    -   Updated documentation to reflect the expanded symbol list and the new session filtering feature.

### Refactor: Dukascopy Data Feed
-   **`fundednext_trading_system/execution/dukascopy_data_feed.py`**:
    -   Refactored the data feed to use the `dukascopy-python` library instead of the `dukascopy-node` command-line tool.
-   **`fundednext_trading_system/requirements.txt`**:
    -   Replaced the `dukascopy-1` git dependency with `dukascopy-python`.
-   **`fundednext_trading_system/tests/test_dukascopy_feed.py`**:
    -   Updated the test to mock the `dukascopy-python` library.
-   **`README.md`**:
    -   Updated documentation to reflect the new data feed implementation.

### Refactor: Production Readiness and Cleanup
-   **`fundednext_trading_system/config/settings.py`**:
    -   Changed the default `ENVIRONMENT` from "development" to "production" to ensure the system is production-first.
-   **`fundednext_trading_system/requirements.txt`**:
    -   Restored pinned dependencies to ensure stable, reproducible builds.
-   **`fundednext_trading_system/dev_requirements.txt`**:
    -   Correctly structured to reference `requirements.txt` and only add development-specific dependencies.
-   **Deleted Redundant Files**:
    -   Removed `fundednext_trading_system/notebooks/`
-   **`README.md`**:
    -   Updated documentation to reflect the production-first approach and latest changes.

### Feat: Dukascopy Data, News Sentiment, and Correlation Matrix
-   **`fundednext_trading_system/execution/dukascopy_data_feed.py`**: Added a new data feed from Dukascopy for model training.
-   **`fundednext_trading_system/trading_core/news_sentiment.py`**: Added news sentiment analysis using `yfinance` and `TextBlob`.
-   **`fundednext_trading_system/trading_core/correlation_manager.py`**: Added a correlation matrix to manage risk.
-   **`fundednext_trading_system/trading_core/risk_manager.py`**: Integrated the correlation matrix to block trades in highly correlated assets.
-   **`fundednext_trading_system/trading_core/signal_engine.py`**: Integrated news sentiment to adjust trade confidence.

### Fix: `MetaTrader5` Library Selection and Startup Check
-   **`fundednext_trading_system/execution/mt5_data_feed.py`**: Made `MetaTrader5` library selection explicit based on the `ENVIRONMENT` variable.
-   **`fundednext_trading_system/offline_training/train_model.py`**: Added a startup check for the real `MetaTrader5` library in production.

### Fix: Monte Carlo Validation Logic
-   **`fundednext_trading_system/offline_training/offline_training.py`**: Improved the `MonteCarloValidator` to provide a more realistic simulation.
