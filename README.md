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
- [Troubleshooting](#troubleshooting)
- [Monitoring](#monitoring)
- [Change Log](#change-log)

## Key Features

- **Hybrid Trading Logic**: Combines an ML model for signal generation with a rule-based fallback system.
- **Symbol-Specific Models**: Trains and deploys a unique ML model for each trading symbol.
- **Incremental Training**: Automatically retrains models with new live data to adapt to changing market conditions.
- **Automated Execution**: Interfaces directly with MT5 to execute and manage trades.
- **Advanced Risk Management**: Features include dynamic position sizing, trailing stop-losses, and equity-based kill switches.
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
- Fetch historical data for each trading symbol.
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

## Configuration

The system's behavior is controlled by environment variables.

-   `ENVIRONMENT`: Set to `production` for live trading or `development` for local testing.
-   `ACCOUNT_PHASE`: Set to `CHALLENGE` or `FUNDED` to load the correct risk management rules.

## Troubleshooting

-   **`ModuleNotFoundError`:** This error usually occurs when the project's dependencies are not installed correctly. Make sure you have run the correct `pip install` command for your environment. If you are still seeing the error, try running the command from the root directory of the project.
-   **`TypeError: ExecutionFlags.__init__() missing...`**: This error occurs when the `ExecutionFlags` class is not initialized with all the required arguments. This was fixed in a recent update. If you are still seeing this error, please pull the latest changes from the repository.
-   **Monte Carlo Validation Failures**: If the Monte Carlo validation consistently fails for all symbols, it may indicate an issue with the validation logic or the trading strategy itself. The validation logic was recently updated to be more robust. If you are still seeing this issue, please pull the latest changes.

## Monitoring

-   **Console**: The terminal will display a live heartbeat with key performance indicators.
-   **Logs**: Detailed logs are saved to the `logs/` directory, separated by type (`system.log`, `errors.log`, `trades.log`).

## Change Log

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
