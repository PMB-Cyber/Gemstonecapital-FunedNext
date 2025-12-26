from offline_training.monte_carlo_validator import MonteCarloValidator
import json

def validate_model(trade_returns):
    validator = MonteCarloValidator()

    report = validator.run(trade_returns)

    logger.info("📊 MONTE CARLO VALIDATION RESULT")
    for k, v in report.items():
        logger.info(f"{k}: {v}")

    with open("model_registry/validation_report.json", "w") as f:
        json.dump(report, f, indent=2)

    if not report["passed"]:
        raise RuntimeError("❌ Model failed Monte Carlo validation")

    logger.success("✅ Model passed Monte Carlo validation")
