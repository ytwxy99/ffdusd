import ccxt

# 初始化交易所
exchange = ccxt.binance()  # 以币安为例

# 设置交易对
symbol = 'BTC/USDT'

# 获取订单簿
order_book = exchange.fetch_order_book(symbol)

# 计算委托订单比例
def calculate_order_ratio(order_book, depth=10):
    bids = order_book['bids'][:depth]  # 获取前 depth 个买单
    asks = order_book['asks'][:depth]  # 获取前 depth 个卖单

    # 计算总委托量
    total_bid_amount = sum(bid[1] for bid in bids)  # 买单总量
    total_ask_amount = sum(ask[1] for ask in asks)  # 卖单总量

    # 计算委托订单比例
    if total_bid_amount + total_ask_amount == 0:
        return 0
    ratio = total_bid_amount / (total_bid_amount + total_ask_amount)
    return ratio

# 计算并打印委托订单比例
depth = 10  # 计算前 10 个档位的委托比例
ratio = calculate_order_ratio(order_book, depth)
print(f"委托订单比例（买单/总委托量）: {ratio:.2%}")
