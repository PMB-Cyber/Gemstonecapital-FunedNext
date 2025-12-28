# FundedNext Trading System

This is a sophisticated, automated trading system designed to interact with the MetaTrader 5 (MT5) platform. It leverages a combination of machine learning and rule-based strategies to execute trades, manage risk, and monitor performance in real-time.

## Key Features

- **Hybrid Trading Logic**: Combines an ML model for signal generation with a rule-based fallback system.
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
- **`ml/`**: Contains the machine learning components.
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
    -   **For Production (Windows):**
        ```bash
        pip install -r requirements.txt
        ```
    -   **For Development (macOS/Linux/Windows):**
        Install the mock `MetaTrader5` package and other development tools.
        ```bash
        pip install -r dev_requirements.txt
        ```

### Configuration

All configuration is managed in `fundednext_trading_system/config/settings.py`. The system's behavior is primarily controlled by the `ENVIRONMENT` variable, which can be set via an environment variable or directly in the file.

-   **Production Mode (`ENVIRONMENT = "production"`)**:
    -   Set the `ENVIRONMENT` environment variable to `"production"`.
    -   Set `ACCOUNT_PHASE` to either `"CHALLENGE"` or `"FUNDED"`.
    -   `DRY_RUN` is disabled (`False`).
    -   `EXECUTION_MODE` is `"LIVE"`.
-   **Development Mode (`ENVIRONMENT = "development"`)**:
    -   `DRY_RUN` is enabled (`True`).
    -   `EXECUTION_MODE` is `"PAPER"`.

## How to Run the System

1.  **Ensure MT5 is Running**: The MetaTrader 5 terminal must be open and logged into your trading account.

2.  **Run the Go-Live Validation (Production Only)**:
    Before the first production run, execute the pre-flight validation script to ensure all systems are go.
    ```bash
    python -m fundednext_trading_system.go_live_validation
    ```
    For a detailed checklist, see `fundednext_trading_system/go_live_checklist.md`.

3.  **Run the Main Orchestrator**:
    Execute the `main.py` script from the project root directory.
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
