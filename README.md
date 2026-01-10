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
- **Symbol-Specific Models**: Trains and deploys a unique ML model for each trading symbol.
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

Before running the main system, you need to train the initial machine learning models.

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

### Correlation Matrix
The system uses a correlation matrix to avoid over-exposure to a single market factor. Before a new trade is opened, the `RiskManager` checks if the new symbol is highly correlated with any open positions and blocks the trade if the correlation exceeds the `CORRELATION_THRESHOLD` (default: `0.8`).

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
