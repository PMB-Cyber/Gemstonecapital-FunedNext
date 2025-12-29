# FundedNext Trading System

This is a sophisticated, automated trading system designed to interact with the MetaTrader 5 (MT5) platform. It leverages a combination of machine learning and rule-based strategies to execute trades, manage risk, and monitor performance in real-time.

## Key Features

- **Hybrid Trading Logic**: Combines an ML model for signal generation with a rule-based fallback system.
- **Symbol-Specific Models**: Trains and deploys a unique ML model for each trading symbol, capturing individual market behaviors.
- **Incremental Training**: Automatically retrains models with new live data after a configurable number of trades to adapt to changing market conditions.
- **Automated Execution**: Interfaces directly with MT5 to execute and manage trades.
- **Advanced Risk Management**: Features include dynamic position sizing, trailing stop-losses, partial take-profits, and equity-based kill switches.
- **Real-time Monitoring**: Provides a console-based heartbeat, detailed logging, and Discord integration for remote updates.
- **Session Control**: Manages trading sessions, including daily maintenance and market readiness checks.
- **Centralized Configuration**: Supports distinct configurations for development and production environments through a single, environment-aware `settings.py`.

## System Architecture

The system is built with a modular architecture, separating concerns into distinct components:

- **`main.py`**: The central orchestrator that initializes all components and runs the main trading loop.
- **`config/settings.py`**: The single source of truth for all configuration, including environment control, trading rules, and symbol lists.
- **`trading_core/`**: The brain of the system, housing modules for signal generation (`signal_engine.py`), risk management (`risk_manager.py`), and trade authorization (`trade_gatekeeper.py`).
- **`execution/`**: Handles all interactions with the MT5 platform.
- **`ml/`**: Contains the machine learning components, including model loading and retraining scripts.
- **`offline_training/`**: Houses the main script for the initial training of all symbol-specific models.
- **`monitoring/`**: Provides system monitoring tools, such as the logger, heartbeat, and kill switches.

## Getting Started

### Prerequisites

- Python 3.8+
- MetaTrader 5 terminal installed and running
- A valid MT5 trading account

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd fundednext_trading_system
    ```

2.  **Set up a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    The `MetaTrader5` package is required for live trading and only runs on Windows. For development on macOS or Linux, a mock module is used.

    -   **On Windows (for Live Trading):**
        Install all dependencies, including the official `MetaTrader5` package.
        ```bash
        pip install -r requirements.txt
        pip install -e .
        ```
    -   **On macOS/Linux (for Development):**
        The system includes a mock `MetaTrader5` module to facilitate development. Before installing, you **must** remove or comment out the `metatrader5` line from `fundednext_trading_system/requirements.txt`.
        ```bash
        # Remove/comment out 'metatrader5' in requirements.txt, then run:
        pip install -r dev_requirements.txt
        pip install -e .
        ```

### Configuration

The primary configuration is handled in `fundednext_trading_system/config/settings.py`. The most important setting is `ENVIRONMENT`, which can be set to either `"development"` or `"production"`. This flag controls not only the execution parameters but also which `MetaTrader5` module is loaded.

-   **Production Mode (`ENVIRONMENT = "production"`)**:
    -   Loads the **real, installed `MetaTrader5` package**, enabling live trading.
    -   Set `ACCOUNT_PHASE` to either `"CHALLENGE"` or `"FUNDED"`.
    -   `DRY_RUN` is disabled (`False`).
    -   `EXECUTION_MODE` is `"LIVE"`.
-   **Development Mode (`ENVIRONMENT = "development"`)**:
    -   Uses the **mock `MetaTrader5` module** located in the project directory.
    -   `DRY_RUN` is enabled (`True`), meaning no live orders will be placed.
    -   `ML_MODE` is set to `TRAINING` to allow the model to be updated.
    -   `EXECUTION_MODE` is `"PAPER"`.

## Machine Learning

The system's ML capabilities have been upgraded to support a more robust and adaptive trading strategy.

### Symbol-Specific Model Training

Instead of a single global model, the system now trains a dedicated model for each symbol defined in `ALLOWED_SYMBOLS`. This allows the models to learn the unique characteristics and patterns of each financial instrument.

### Incremental Training

To ensure the models remain relevant in a constantly evolving market, the system implements incremental training. After a symbol has executed a predefined number of trades (configurable via `RETRAIN_AFTER_N_TRADES` in `settings.py`), a retraining process is automatically triggered. This process fetches the latest market data, appends it to the historical dataset, and retrains the model for that specific symbol.

## How to Run the System

1.  **Ensure MT5 is Running**: The MetaTrader 5 terminal must be open and logged into your trading account.

2.  **Initial Model Training**:
    Before running the main system for the first time, you must train the initial set of ML models. This script will fetch historical data for each symbol, train a model, and save it to the `fundednext_trading_system/models/` directory.
    ```bash
    python -m fundednext_trading_system.offline_training.train_model
    ```

3.  **Run the Go-Live Validation (Production Only)**:
    Before the first production run, execute the pre-flight validation script to ensure all systems are go.
    ```bash
    python -m fundednext_trading_system.go_live_validation
    ```
    For a detailed checklist, see `fundednext_trading_system/go_live_checklist.md`.

4.  **Run the Main Orchestrator**:
    Execute the `main.py` script from the project root directory. The system will now load the symbol-specific models and begin trading.
    ```bash
    python -m fundednext_trading_system.main
    ```

### Monitoring

-   **Console**: The terminal will display a live heartbeat with key performance indicators.
-   **Logs**: Detailed, structured logs are saved to the `logs/` directory, separated by type (`system.log`, `errors.log`, `trades.log`).

## Risk Management

The system includes several layers of risk control, all configurable in `config/settings.py`:
-   **Position Sizing**: Dynamically calculated based on risk tolerance.
-   **Trailing Stop-Loss**: ATR-based trailing stops to lock in profits.
-   **Partial Take-Profits**: Predefined profit targets for partial position closes.
-   **Equity Kill Switch**: Halts trading if equity drops below a critical threshold.
-   **Profit Lock**: Pauses trading after a daily profit target is achieved.
