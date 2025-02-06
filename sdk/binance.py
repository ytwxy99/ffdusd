import ccxt

# 初始化币安交易所实例
def auth_exchagne_binance(ak, sk, is_enable_rate_limit):
    return ccxt.binance({
        'apiKey': ak,
        'secret': sk, 
        'enableRateLimit': is_enable_rate_limit,  # 启用速率限制
    })


# 查询现价
def fetch_current_price(exchange, symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        last_price = ticker['last']
        print(f"Current price of {symbol}: {last_price}")
        return last_price
    except Exception as e:
        print(f"Error fetching current price: {e}")
        return None


# 查询symbol信息
def fetch_symbol_market(exchange, symbol):
    import pdb;pdb.set_trace()
    return exchange.fetch_market(symbol)
