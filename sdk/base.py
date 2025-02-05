import ccxt

def load_markets():
    binance = ccxt.binance()
    binance.load_markets()
