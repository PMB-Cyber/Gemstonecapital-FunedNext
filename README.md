# FundedNext Trading System

This is a sophisticated, automated trading system designed to interact with the MetaTrader 5 (MT5) platform. It leverages a combination of machine learning and rule-based strategies to execute trades, manage risk, and monitor performance in real-time.

## Key Features

- **Hybrid Trading Logic**: Combines an ML model for signal generation with a rule-based fallback system.
- **Automated Execution**: Interfaces directly with MT5 to execute and manage trades.
- **Advanced Risk Management**: Features include dynamic position sizing, trailing stop-losses, partial take-profits, and equity-based kill switches.
- **Real-time Monitoring**: Provides a console-based heartbeat, detailed logging, and Discord integration for remote updates.
- **Session Control**: Manages trading sessions, including daily maintenance and market readiness checks.
- **Development & Production Environments**: Supports distinct configurations for safe development/testing (`DRY_RUN` mode) and live trading.

## System Architecture

The system is built with a modular architecture, separating concerns into distinct components:

- **`main.py`**: The central orchestrator that initializes all components and runs the main trading loop.
- **`config/`**: Contains all configuration files, including `settings.py` for environment control and `allowed_symbols.py`.
- **`trading_core/`**: The brain of the system, housing modules for signal generation (`signal_engine.py`), risk management (`risk_manager.py`), and trade authorization (`trade_gatekeeper.py`).
- **`execution/`**: Handles all interactions with the MT5 platform, including data feeds (`mt5_data_feed.py`), order routing (`order_router.py`), and position management (`trailing_sl_manager.py`, `partial_tp_manager.py`).
- **`ml/`**: Contains the machine learning components, including the inference router (`ml_router.py`) and logic for offline model training.
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
    The `MetaTrader5` package has specific platform requirements.

    -   **On Windows:**
        ```bash
        pip install -r requirements.txt
        ```
    -   **On macOS/Linux:**
        A mock `MetaTrader5` module is provided for development purposes. You may need to remove the `metatrader5` line from `requirements.txt` before installing.
        ```bash
        # (Optional) Remove/comment out 'metatrader5' in requirements.txt
        pip install -r requirements.txt
        ```

### Configuration

The primary configuration is handled in `fundednext_trading_system/config/settings.py`. The most important setting is `ENVIRONMENT`, which can be set to either `"development"` or `"production"`.

-   **Development Mode (`ENVIRONMENT = "development"`)**:
    -   `DRY_RUN` is enabled (`True`), meaning no live orders will be placed.
    -   `ML_MODE` is set to `TRAINING` to allow the model to be updated.
-   **Production Mode (`ENVIRONMENT = "production"`)**:
    -   `DRY_RUN` is disabled (`False`).
    -   `ML_MODE` is set to `INFERENCE`, using the pre-trained model without updates.

## How to Run the System

1.  **Ensure MT5 is Running**: The MetaTrader 5 terminal must be open and logged into your trading account.

2.  **Run the Main Orchestrator**:
    Execute the `main.py` script from the project root directory.
    ```bash
    python -m fundednext_trading_system.main
    ```

    The system will perform a series of startup checks, initialize all components, and begin the trading loop.

### Monitoring

-   **Console**: The terminal will display a live "heartbeat" with key performance indicators, including account equity, open positions, and risk metrics.
-   **Logs**: Detailed logs are saved to the `logs/` directory, providing a granular record of all system activities.
-   **Discord**: The system can be configured to send real-time updates to a Discord channel (see `monitoring/discord_logger.py`).

## Risk Management

The system includes several layers of risk control:

-   **Position Sizing**: Volume is calculated based on the account's risk tolerance and the trade's stop-loss.
-   **Trailing Stop-Loss**: Stop-losses are dynamically adjusted using the Average True Range (ATR) to lock in profits.
-   **Partial Take-Profits**: Positions can be partially closed at predefined profit targets.
-   **Equity Kill Switch**: Trading is automatically halted if account equity drops below a critical threshold.
-   **Profit Lock**: Protects daily profits by pausing trading after a certain gain is achieved.

## Development & Testing

-   **Dry Run Mode**: To test the system's logic without placing real trades, ensure `ENVIRONMENT` is set to `"development"` in `config/settings.py`.
-   **Offline Training**: The ML model can be trained and evaluated offline using scripts in the `offline_training/` directory.
-   **Validation Scripts**: The `tests/` directory contains scripts for validating specific system components. These are not unit tests but rather functional checks.
