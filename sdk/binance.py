import ccxt

from models.base import Market, session
from models import markets

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
        return last_price
    except Exception as e:
        print(f"Error fetching current price: {e}")
        return None


# 查询symbol信息
def fetch_symbol_market(exchange, symbol):
    return exchange.fetch_market(symbol)


# 查询所有委托单
def fetch_open_orders(exchange, symbol):
    try:
        return exchange.fetch_open_orders(symbol)
    except ccxt.BaseError as e:
        print(f"Error fetching open orders: {e}")
        return []


# 撤销指定的订单
def cancel_order(exchange, symbol, order_id):
    try:
        cancel_result = exchange.cancel_order(order_id, symbol)
        print(f"Cancel order result: {cancel_result}")
        return cancel_result
    except ccxt.BaseError as e:
        print(f"Error canceling order: {e}")
        return None


# 现货买入
def create_buy_limit_order(exchange, symbol, amount, price, sell_price):
    try:
        order = exchange.create_limit_buy_order(symbol, amount, price)
        if order:
            order_id = order["info"]["orderid"]
            side = order["info"]["side"]
            status = order["info"]["status"]

            new_order = Market(order_id=order_id, side=side, status=status, sell_price=sell_price, price=price)
            markets.create_order(session, new_order)
            print(f"Buy order created, order_id: {order_id}, price: {price}")
            return order["info"], True

    except ccxt.BaseError as e:
        print(f"Error creating buy order: {e}")
        return None, False


# 现货卖出
def create_sell_limit_order(exchange, symbol, amount, price, peer_order_id):
    try:
        order = exchange.create_limit_sell_order(symbol, amount, price)
        if order:
            order_id = order["info"]["orderid"]
            side = order["info"]["side"]
            status = order["info"]["status"]

            new_order = Market(order_id=order_id, side=side, status=status, sell_price=price, price=price, peer_order_id=peer_order_id)
            markets.create_order(session, new_order)
            print(f"Sell order created, order_id: {order_id}, price: {price}")
            return order["info"], True

    except ccxt.BaseError as e:
        print(f"Error creating sell order: {e}")
        return None, False


def check_order_status(exchange, order_id, symbol):
    try:
        order = exchange.fetch_order(order_id, symbol)
        return order
    except ccxt.BaseError as e:
        print(f"Error fetching order status: {e}")
        return None


def get_first_order_book(exchange, symbol):
    book = {
        "sell_price": 0.0,
        "buy_price": 0.0,
        "sell_count": 0.0,
        "buy_count": 0.0,
    }

    try:
        order_book = exchange.fetch_order_book(symbol)
        # 提取买盘（bids）和卖盘（asks）
        bids = order_book['bids']
        asks = order_book['asks']

        # 打印盘口基础信息
        book["buy_price"] = float(bids[0][0])
        book["buy_count"] = bids[0][1]
        book["sell_price"] = asks[0][0]
        book["sell_count"] = asks[0][1]

        return book

    except ccxt.NetworkError as e:
        print(f"网络错误: {e}")
        book = None
        return book

    except ccxt.ExchangeError as e:
        print(f"交易所错误: {e}")
        book = None
        return book

    except Exception as e:
        print(f"未知错误: {e}")
        book = None
        return book

