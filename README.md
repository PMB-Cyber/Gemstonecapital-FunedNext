# FundedNext Trading System

This is a sophisticated, automated trading system designed for the FundedNext 5k challenge and beyond. It features a **Hybrid Strategy** combining four specialized trading logics with a dual-layer Machine Learning gatekeeper.

## Table of Contents

- [Key Features](#key-features)
- [Hybrid Trading Strategy](#hybrid-trading-strategy)
- [Dual-Layer ML Logic](#dual-layer-ml-logic)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Operational Instructions](#operational-instructions)
  - [1. MT5 Pepperstone Setup](#1-mt5-pepperstone-setup)
  - [2. Automated Parameter Optimization](#2-automated-parameter-optimization)
  - [3. Initial Model Training](#3-initial-model-training)
  - [4. Go-Live Validation](#4-go-live-validation)
  - [5. Run the Main Orchestrator](#5-run-the-main-orchestrator)
- [System Architecture](#system-architecture)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Change Log](#change-log)

## Key Features

- **Hybrid Scalping Strategy**: Combines Momentum, Mean Reversion, Pullback, and Breakout logics.
- **50 Symbols Support**: Pre-configured for a diverse portfolio of 50 instruments (Forex, Indices, Commodities, Crypto).
- **Automated Optimization**: Built-in grid search to find the best indicator parameters per individual symbol.
- **Dual-Layer ML Gatekeeper**: Rules generate baseline signals; ML confirms or rejects them based on probability.
- **High-Precision Data**: Uses real MT5 Tick Data for training and optimization in production.
- **Regime Detection**: Automatically switches logic based on Trend, Range, or High Volatility regimes.
- **Advanced Risk Management**: Dynamic position sizing, trailing stop-losses, and correlation-based filtering.

## Hybrid Trading Strategy

The system monitors 50 symbols on the **M5 (5-minute)** timeframe using four primary strategies:

1.  **Momentum**: Captures strong trends using ADX thresholds and EMA crossovers.
2.  **Mean Reversion**: Identifies overextended moves using Bollinger Bands and RSI oversold/overbought levels.
3.  **Pullback**: Enters on retracements to key EMAs within a confirmed trend.
4.  **Breakout**: Capitalizes on volatility expansions and price breaks above/below recent High/Low ranges.

## Dual-Layer ML Logic

The system operates with a probabilistic confirmation layer:

-   **Layer 1 (Rules)**: The rule-based engine scans the market for the 4 hybrid setups.
-   **Layer 2 (ML Gatekeeper)**: If a rule-based setup is found, the ML model (Gradient Boosting) provides a probability. The trade only proceeds if ML confirms the direction with > 70% confidence.
-   **Failover**:
    -   If the ML pipeline fails (e.g., model missing), the system falls back to pure high-confidence rule signals (> 80%).
    -   If rules fail to trigger but ML sees an extremely high-probability setup (> 90%), it can generate a backup signal.

## Getting Started

### Prerequisites

-   Windows OS (for production MT5 interaction).
-   Python 3.8+.
-   MetaTrader 5 terminal with a **Pepperstone** account (Demo or Live).

### Installation

1.  **Install Production Dependencies:**
    ```bash
    pip install -r fundednext_trading_system/requirements.txt
    ```

## Operational Instructions

### 1. MT5 Pepperstone Setup
1.  Open your Pepperstone MT5 terminal.
2.  Ensure "Algo Trading" is enabled (Green button).
3.  Go to `Tools -> Options -> Expert Advisors` and check "Allow Algorithmic Trading".
4.  Ensure all 50 symbols are visible in the Market Watch.

### 2. Automated Parameter Optimization
Before training models, find the best settings for each symbol:
```bash
# This is integrated into the training script, but can be run independently if needed.
python -m fundednext_trading_system.offline_training.train_model
```
The system will run a grid search for each symbol to find optimal EMA and RSI settings and update `config/symbols_config.py`.

### 3. Initial Model Training
The training script fetches real tick data from Pepperstone MT5:
```bash
python -m fundednext_trading_system.offline_training.train_model
```
-   Fetches raw ticks.
-   Aggregates to M5 candles.
-   Optimizes indicators.
-   Trains ML models.
-   Validates via Monte Carlo simulation.

### 4. Go-Live Validation
Run the pre-flight check:
```bash
python -m fundednext_trading_system.go_live_validation
```

### 5. Run the Main Orchestrator
Start the live trading loop:
```bash
ACCOUNT_PHASE=CHALLENGE python -m fundednext_trading_system.main
```

## Configuration

-   `config/settings.py`: Global settings, symbols, and session times.
-   `config/symbols_config.py`: Symbol-specific optimized indicator parameters.
-   `ENVIRONMENT`: Defaults to `production`.

## Change Log

### Expansion to Hybrid 50-Symbol Strategy
-   **Expanded symbols to 50**: Added AUDUSD, BTCUSD, ETHUSD, and various indices/commodities.
-   **Hybrid Signal Engine**: Implemented Mean Reversion, Momentum, Pullback, and Breakout logics in `signal_engine.py`.
-   **Automated Optimizer**: Added `optimizer.py` for per-symbol grid search optimization.
-   **Tick Data Integration**: Updated `mt5_data_feed.py` to support `copy_ticks_from` and aggregation.
-   **Dual-Layer Orchestrator**: Updated `main.py` with the ML gatekeeper and failover logic.
-   **M5 Scalping Focus**: Shifted all strategy logic and data fetching to the 5-minute timeframe.
