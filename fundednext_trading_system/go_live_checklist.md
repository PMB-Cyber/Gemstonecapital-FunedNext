# Pre-Flight Go-Live Checklist

This checklist must be completed before deploying the trading system to a live production environment.

## 1. Configuration Verification

- [ ] **Environment Variables**:
  - [ ] `ENVIRONMENT` is set to `"production"`.
  - [ ] `ACCOUNT_PHASE` is set to either `"CHALLENGE"` or `"FUNDED"`.
- [ ] **`config/settings.py`**:
  - [ ] `DRY_RUN` is `False`.
  - [ ] `EXECUTION_MODE` is `"LIVE"`.
  - [ ] `ML_MODE` is `"INFERENCE"`.
  - [ ] `ALLOWED_SYMBOLS` are correct for the target account.
  - [ ] All risk parameters in `PHASE_RULES` are confirmed to match the prop firm's rules.

## 2. Dependency & Environment Check

- [ ] **`requirements.txt`**:
  - [ ] Production dependencies are frozen and correct.
  - [ ] No development-specific packages (e.g., `pylint`, `notebook`) are included.
- [ ] **Python Environment**:
  - [ ] The environment is clean and uses only packages from `requirements.txt`.
- [ ] **`MetaTrader5` Package**:
  - [ ] The official `MetaTrader5` package is installed (not the mock version).

## 3. Pre-Launch Validation

- [ ] **Run `go_live_validation.py`**:
  - [ ] Execute the script: `python -m fundednext_trading_system.go_live_validation`.
  - [ ] Confirm that all checks pass with "✅" and there are no "❌ FATAL" errors.
  - [ ] Address any warnings or failures before proceeding.
- [ ] **MT5 Terminal**:
  - [ ] The MetaTrader 5 terminal is running and logged into the correct account.
  - [ ] "Algo Trading" is enabled.
- [ ] **Manual Sanity Check**:
  - [ ] Verify that there are no open positions or pending orders on the account.
  - [ ] Confirm that the account equity is correct.

## 4. Final Launch

- [ ] **Start the System**:
  - [ ] Run the main orchestrator: `python -m fundednext_trading_system.main`.
- [ ] **Initial Monitoring**:
  - [ ] Monitor the console heartbeat for the first 15 minutes to ensure stability.
  - [ ] Check `logs/system.log` and `logs/errors.log` for any unexpected messages.
  - [ ] Confirm that Discord notifications (if enabled) are being received.

---
*Checklist completed by: ____________________*
*Date: ____________________*
