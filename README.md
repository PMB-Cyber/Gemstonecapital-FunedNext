# FundedNext Trading System

This is a sophisticated, automated trading system designed to interact with the MetaTrader 5 (MT5) platform. It leverages a combination of machine learning and rule-based strategies to execute trades, manage risk, and monitor performance in real-time.

## Table of Contents

- [Key Features](#key-features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [How to Run the System](#how-to-run-the-system)
  - [1. Initial Model Training](#1-initial-model-training)
  - [2. Go-Live Validation (Production Only)](#2-go-live-validation-production-only)
  - [3. Run the Main Orchestrator](#3-run-the-main-orchestrator)
- [System Architecture](#system-architecture)
- [Configuration](#configuration)
- [Environments: Production vs. Development](#environments-production-vs-development)
- [Troubleshooting](#troubleshooting)
- [Monitoring](#monitoring)
- [Change Log](#change-log)

## Key Features

- **Hybrid Trading Logic**: Combines an ML model for signal generation with a rule-based fallback system.
- **Symbol-Specific Models**: Trains and deploys a unique ML model for each trading symbol.
- **Incremental Training**: Automatically retrains models with new live data to adapt to changing market conditions.
- **Automated Execution**: Interfaces directly with MT5 to execute and manage trades.
- **Advanced Risk Management**: Features include dynamic position sizing, trailing stop-losses, equity-based kill switches, and correlation-based trade blocking.
- **News Sentiment Analysis**: Integrates news sentiment into the signal generation process to adjust trade confidence.
- **Real-time Monitoring**: Provides a console-based heartbeat, detailed logging, and Discord integration.
- **Centralized Configuration**: Supports distinct configurations for development and production through environment variables.

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
        This command installs all the production dependencies, plus additional tools for development.

## How to Run the System

### 1. Initial Model Training

Before you can run the main trading system, you need to train the initial machine learning models. This is done by running the `train_model.py` script.

**Important**: The model training process now uses historical data from Dukascopy and requires the `dukascopy-1` command-line tool to be installed and available in your system's PATH.

-   **On Windows (Production):**
    To run the training script on Windows and use the real `MetaTrader5` library, you **must** set the `ENVIRONMENT` environment variable to `production`.

    In Command Prompt:
    ```cmd
    set ENVIRONMENT=production
    python -m fundednext_trading_system.offline_training.train_model
    ```

    In PowerShell:
    ```powershell
    $env:ENVIRONMENT="production"
    python -m fundednext_trading_system.offline_training.train_model
    ```

-   **On macOS/Linux (Development):**
    ```bash
    ENVIRONMENT=development python -m fundednext_trading_system.offline_training.train_model
    ```

This script will:
- Fetch historical data for each trading symbol from Dukascopy.
- Train a unique model for each symbol.
- Save the trained models to the `fundednext_trading_system/models/` directory.

### 2. Go-Live Validation (Production Only)

Before running the system in a live trading environment, it's crucial to run the pre-flight validation script. This script performs several important safety checks to ensure that the system is ready for live trading.

```bash
ENVIRONMENT=production python -m fundednext_trading_system.go_live_validation
```

### 3. Run the Main Orchestrator

Once the initial models are trained, you can run the main trading system.

-   **Production Example:**
    ```bash
    ENVIRONMENT=production ACCOUNT_PHASE=CHALLENGE python -m fundednext_trading_system.main
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

The system includes several layers of risk management to protect capital and adhere to the rules of prop trading firms like FundedNext.

### Correlation Matrix

To avoid over-exposure to a single market factor, the system includes a correlation-based risk check.

-   **How it Works**: On startup, the `CorrelationManager` fetches 30 days of historical data for all allowed symbols and computes a correlation matrix of their returns. This calculation runs in a background thread to avoid delaying the application's startup.
-   **Trade Blocking**: Before a new trade is opened, the `RiskManager` checks the correlation between the new symbol and all currently open positions. If the absolute correlation with any open position exceeds a defined threshold, the trade is blocked.
-   **Configuration**: The correlation threshold can be configured in `fundednext_trading_system/config/settings.py` via the `CORRELATION_THRESHOLD` variable. The default is `0.8`.

## News Sentiment Analysis

The system incorporates a news sentiment analysis layer to gauge market mood and adjust its trading strategy accordingly.

-   **Data Source**: News headlines are fetched from Yahoo Finance using the `yfinance` library.
-   **Sentiment Analysis**: The sentiment of each headline is analyzed using the `TextBlob` library, which provides a polarity score (ranging from -1.0 for negative to 1.0 for positive).
-   **Integration**: The aggregate sentiment score for a given symbol is fed into the `SignalEngine`. This score is used to adjust the confidence level of the rule-based trading signals. A positive sentiment will increase the confidence of a "buy" signal, while a negative sentiment will increase the confidence of a "sell" signal.

## Configuration

The system's behavior is controlled by environment variables.

-   `ENVIRONMENT`: Set to `production` for live trading or `development` for local testing.
-   `ACCOUNT_PHASE`: Set to `CHALLENGE` or `FUNDED` to load the correct risk management rules.

## Environments: Production vs. Development

The `ENVIRONMENT` variable is the most critical setting in the system. It controls which `MetaTrader5` library is used.

-   **`ENVIRONMENT=production`**:
    -   Uses the **real `MetaTrader5` library**. This is required for live trading and for getting real-world data.
    -   This mode is **only available on Windows**.
    -   If you are on Windows and want to use the system with your actual `MetaTrader5` terminal, you **must** set this variable.

-   **`ENVIRONMENT=development`**:
    -   Uses a **mock `MetaTrader5` library**. This allows you to run the system on non-Windows machines (like macOS or Linux) for development and testing purposes.
    -   The mock library does not connect to a real `MetaTrader5` terminal and provides simulated data.

## Troubleshooting

-   **`ModuleNotFoundError: No module named 'MetaTrader5'`**: This error will occur if you try to run the system with `ENVIRONMENT=production` on a non-Windows machine, or if the `MetaTrader5` library is not installed correctly.
-   **`TypeError: ExecutionFlags.__init__() missing...`**: This error occurs when the `ExecutionFlags` class is not initialized with all the required arguments. This was fixed in a recent update. If you are still seeing this error, please pull the latest changes from the repository.
-   **Monte Carlo Validation Failures**: If the Monte Carlo validation consistently fails for all symbols, it may indicate an issue with the validation logic or the trading strategy itself. The validation logic was recently updated to be more robust. If you are still seeing this issue, please pull the latest changes.

## Monitoring

-   **Console**: The terminal will display a live heartbeat with key performance indicators.
-   **Logs**: Detailed logs are saved to the `logs/` directory, separated by type (`system.log`, `errors.log`, `trades.log`).

## Change Log

### Feat: Dukascopy Data, News Sentiment, and Correlation Matrix

-   **`fundednext_trading_system/execution/dukascopy_data_feed.py`**:
    -   Added a new data feed to fetch historical data from Dukascopy for model training.
-   **`fundednext_trading_system/trading_core/news_sentiment.py`**:
    -   Added a new module to perform news sentiment analysis using `yfinance` and `TextBlob`.
-   **`fundednext_trading_system/trading_core/correlation_manager.py`**:
    -   Added a new module to calculate the correlation matrix of asset returns.
-   **`fundednext_trading_system/trading_core/risk_manager.py`**:
    -   Integrated the correlation matrix to prevent opening trades in highly correlated assets.
-   **`fundednext_trading_system/trading_core/signal_engine.py`**:
    -   Integrated the news sentiment score to adjust the confidence of trading signals.
-   **`fundednext_trading_system/main.py`**:
    -   Updated the main orchestrator to pass the necessary data to the `RiskManager`.
-   **`fundednext_trading_system/config/settings.py`**:
    -   Added a new `CORRELATION_THRESHOLD` setting.
-   **`fundednext_trading_system/requirements.txt`**:
    -   Added new dependencies: `yfinance`, `textblob`, `loguru`, `pandas`, and `dukascopy-1`.
-   **`README.md`**:
    -   Updated the documentation to reflect the new features and changes.

### Fix: `MetaTrader5` Library Selection and Startup Check

-   **`fundednext_trading_system/execution/mt5_data_feed.py`**:
    -   Made the `MetaTrader5` library selection explicit based on the `ENVIRONMENT` variable.
-   **`fundednext_trading_system/offline_training/train_model.py`**:
    -   Added a startup check to ensure the real `MetaTrader5` library is available when `ENVIRONMENT=production`.
-   **`README.md`**:
    -   Added a new section to explain the difference between the production and development environments.

### Fix: Monte Carlo Validation Logic

-   **`fundednext_trading_system/offline_training/offline_training.py`**:
    -   Improved the `MonteCarloValidator` to shuffle trade returns instead of resampling with replacement, providing a more realistic simulation.
-   **`README.md`**:
    -   Added a note to the troubleshooting section about Monte Carlo validation failures.

### Fix: `TypeError` in `train_model.py` and `MetaTrader5` Module Usage

-   **`fundednext_trading_system/offline_training/train_model.py`**:
    -   Provided the missing `account_phase` and `execution_mode` arguments to the `ExecutionFlags` class.
-   **`README.md`**:
    -   Added clear instructions for running the training script on Windows with the production environment.
    -   Added the `TypeError` to the troubleshooting section.

### Fix: `ModuleNotFoundError` and Project Simplification

-   **`fundednext_trading_system/offline_training/train_model.py`**:
    -   Corrected a typo in the `if __name__ == "__main__":` block.
-   **`fundednext_trading_system/requirements.txt` and `fundednext_trading_system/dev_requirements.txt`**:
    -   Added the `-e .` flag to both files to automatically install the project in editable mode.
-   **`README.md`**:
    -   Removed the separate `pip install -e .` step from the installation instructions.
    -   Restructured the `README.md` to be more beginner-friendly.
-   **Deleted Files**:
    -   `main_output.log`
    -   `model.pkl`
    -   `stats.pkl`
    -   `fundednext_trading_system/check_dataset.py`
    -   `fundednext_trading_system/dry_run_report.py`
    -   `fundednext_trading_system/test_mt5.py`
-   **`.gitignore`**:
    -   Added `*.pkl` to the `.gitignore` file.
