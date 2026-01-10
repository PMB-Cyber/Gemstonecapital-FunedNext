from fundednext_trading_system.ml.retraining.collect_recent_data import collect
from fundednext_trading_system.ml.retraining.retrain_model import retrain
from fundednext_trading_system.ml.retraining.validate_model import validate
from fundednext_trading_system.ml.retraining.monte_carlo import monte_carlo_test

SYMBOLS = ["EURUSD","GBPUSD","USDJPY","XAUUSD","US30","NDX100"]

def run_pipeline():
    for symbol in SYMBOLS:
        collect(symbol)
        retrain(symbol)
        validate(symbol)
        monte_carlo_test(symbol)

if __name__ == "__main__":
    run_pipeline()
    
if new_model.sharpe > live_model.sharpe and \
   new_model.max_dd < live_model.max_dd:
    deploy_model()
else:
    keep_live_model()
