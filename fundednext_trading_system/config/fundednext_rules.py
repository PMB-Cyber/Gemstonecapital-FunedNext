from config.trading_mode import TRADING_MODE

if TRADING_MODE == "CHALLENGE":
    from config.fundednext_challenge import *
else:
    from config.fundednext_funded import *
