# FundedNext Trading System

This is a Python-based trading system designed to interact with the MetaTrader 5 (MT5) platform.

## Setup

### 1. Create a Virtual Environment

It is highly recommended to use a virtual environment to manage project dependencies.

```bash
python -m venv venv
```

### 2. Activate the Virtual Environment

- **On Windows:**
  ```bash
  .\venv\Scripts\activate
  ```

- **On macOS and Linux:**
  ```bash
  source venv/bin/activate
  ```

### 3. Install Dependencies

Install the required packages using pip:

```bash
pip install -r fundednext_trading_system/requirements.txt
```

In a development environment, you may need to install the mock `MetaTrader5` package:

```bash
pip install -e fundednext_trading_system/MetaTrader5
```

## How to Run

To start the application, run the `main` module from the **root of the project** using the `-m` flag:

```bash
python -m fundednext_trading_system.main
```

This ensures that the Python interpreter treats the `fundednext_trading_system` directory as a package, which is necessary for the imports to work correctly.

## Go Live Checklist

The `go_live_checklist.md` file is a Markdown document that outlines the steps to take before deploying the system to a live environment. It is not an executable Python script.
