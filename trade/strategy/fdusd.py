from sdk import binance

def do(exchange, symbol):
    binance.fetch_current_price(exchange, symbol)
    print(binance.fetch_symbol_market(exchange, symbol))
