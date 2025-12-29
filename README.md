# FundedNext Trading System

This is a sophisticated, automated trading system designed to interact with the MetaTrader 5 (MT5) platform. It leverages a combination of machine learning and rule-based strategies to execute trades, manage risk, and monitor performance in real-time.

## Key Features

- **Hybrid Trading Logic**: Combines an ML model for signal generation with a rule-based fallback system.
- **Symbol-Specific Models**: Trains and deploys a unique ML model for each trading symbol.
- **Incremental Training**: Automatically retrains models with new live data to adapt to changing market conditions.
- **Automated Execution**: Interfaces directly with MT5 to execute and manage trades.
- **Advanced Risk Management**: Features include dynamic position sizing, trailing stop-losses, and equity-based kill switches.
- **Real-time Monitoring**: Provides a console-based heartbeat, detailed logging, and Discord integration.
- **Centralized Configuration**: Supports distinct configurations for development and production through environment variables.

## Quick Start

1.  **Install Dependencies**:
    -   **Production (Windows)**: `pip install -r requirements.txt`
    -   **Development (macOS/Linux)**: `pip install -r dev_requirements.txt`
2.  **Train Initial Models**:
    ```bash
    ENVIRONMENT=development python -m fundednext_trading_system.offline_training.train_model
    ```
3.  **Run Go-Live Validation (Production Only)**:
    ```bash
    ENVIRONMENT=production python -m fundednext_trading_system.go_live_validation
    ```
4.  **Run the System**:
    ```bash
    # Set ENVIRONMENT and ACCOUNT_PHASE as needed
    ENVIRONMENT=production ACCOUNT_PHASE=CHALLENGE python -m fundednext_trading_system.main
    ```

---

## System Architecture

The system is built with a modular architecture, separating concerns into distinct components:

-   **`main.py`**: The central orchestrator that runs the main trading loop.
-   **`config/settings.py`**: The single source of truth for all configuration.
-   **`trading_core/`**: The brain of the system, housing modules for signal generation, risk management, and trade authorization.
-   **`execution/`**: Handles all interactions with the MT5 platform.
-   **`ml/`**: Contains the machine learning components, including model loading and retraining scripts.
-   **`offline_training/`**: Houses the script for the initial training of all symbol-specific models.
-   **`monitoring/`**: Provides system monitoring tools, such as the logger and kill switches.

## Configuration

The system's behavior is primarily controlled by two environment variables:

-   `ENVIRONMENT`: Set to `"production"` for live trading or `"development"` for local testing. This is the **most critical setting**, as it controls which `MetaTrader5` module is loaded, enables or disables dry runs, and sets the ML mode.
-   `ACCOUNT_PHASE`: Set to `"CHALLENGE"` or `"FUNDED"` to load the correct risk management rules from `config/settings.py`.

### Environment-Specific Behavior

| Setting          | `ENVIRONMENT="production"` | `ENVIRONMENT="development"` |
| ---------------- | -------------------------- | --------------------------- |
| **`DRY_RUN`**    | `False` (Live Trades)      | `True` (No Trades)          |
| **`EXECUTION_MODE`** | `"LIVE"`                 | `"PAPER"`                 |
| **`ML_MODE`**    | `"INFERENCE"`              | `"TRAINING"`                |
| **`MetaTrader5`**| Real, installed package    | Mock, local module          |

## Installation and Setup

### Prerequisites

-   Python 3.8+
-   MetaTrader 5 terminal installed and running (for production)

### Dependencies

The project maintains two separate dependency files:

-   `requirements.txt`: Contains the exact, minimal packages required for a **live production environment**.
-   `dev_requirements.txt`: Includes all production packages plus additional tools for development, such as `notebook`, `pylint`, and `black`.

#### On Windows (Production)

For live trading, the official `MetaTrader5` package is required, which is only available on Windows.

```bash
pip install -r requirements.txt
```

#### On macOS/Linux (Development)

The system includes a mock `MetaTrader5` module to facilitate development on non-Windows systems. **Do not** attempt to install the `metatrader5` package from `requirements.txt`, as it will fail.

```bash
pip install -r dev_requirements.txt
```

## How to Run the System

### 1. Initial Model Training

Before running the main system for the first time, you must train the initial set of ML models. This script will fetch historical data for each symbol, train a model, and save it to the `fundednext_trading_system/models/` directory.

It is recommended to run this in the `development` environment to use the mock MT5 module and avoid hitting rate limits.

```bash
ENVIRONMENT=development python -m fundednext_trading_system.offline_training.train_model
```

### 2. Go-Live Validation (Production Only)

Before every production run, execute the pre-flight validation script. This script performs critical safety checks to ensure the system is ready for live trading. It verifies:
- MT5 connectivity
- The absence of open positions
- Correct configuration (`ENVIRONMENT="production"`)
- The state of all kill switches and risk locks

```bash
ENVIRONMENT=production python -m fundednext_trading_system.go_live_validation
```

For a detailed checklist of manual steps, see `fundednext_trading_system/go_live_checklist.md`.

### 3. Run the Main Orchestrator

Execute the `main.py` script from the project root directory. The system will load the symbol-specific models and begin trading according to the configured environment.

-   **Production Example**:
    ```bash
    ENVIRONMENT=production ACCOUNT_PHASE=CHALLENGE python -m fundednext_trading_system.main
    ```
-   **Development Example**:
    ```bash
    ENVIRONMENT=development python -m fundednext_trading_system.main
    ```

## Monitoring

-   **Console**: The terminal will display a live heartbeat with key performance indicators.
-   **Logs**: Detailed logs are saved to the `logs/` directory, separated by type (`system.log`, `errors.log`, `trades.log`).
