from sdk import binance

SYMBOL = 'FDUSD/USDT'
exchange = None

def init_trade(conf, is_enable_rate_limit):
    global exchange
    exchange = binance.auth_exchagne_binance(conf['AUTH']['ak'], conf['AUTH']['sk'], True)

    return exchange
