import ccxt

# 选择交易所（这里以币安为例，你可以替换为其他交易所）
exchange = ccxt.binance({
    'enableRateLimit': True,  # 启用速率限制避免被封禁
    # 如果需要代理，取消下面两行注释并替换为你的代理地址
    # 'proxies': {
    #     'http': 'http://your-proxy.com:8080',
    #     'https': 'http://your-proxy.com:8080',
    # }
})

try:
    # 获取 FDUSD/USDT 的盘口数据
    order_book = exchange.fetch_order_book('FDUSD/USDT')

    # 提取买盘（bids）和卖盘（asks）
    bids = order_book['bids']
    asks = order_book['asks']

    # 打印前5档买盘和卖盘
    print("当前买盘（Bids）:")
    for bid in bids[:100]:
        price, amount = bid[:2]
        print(f"价格: {price:.6f} 数量: {amount:.2f}")

    print("\n当前卖盘（Asks）:")
    for ask in asks[:100]:
        price, amount = ask[:2]
        print(f"价格: {price:.6f} 数量: {amount:.2f}")

    # 打印盘口基础信息
    print(f"\n盘口时间: {order_book['timestamp']}")
    print(f"买盘最高价: {bids[0][0]:.6f} (数量: {bids[0][1]:.2f})")
    print(f"卖盘最低价: {asks[0][0]:.6f} (数量: {asks[0][1]:.2f})")

except ccxt.NetworkError as e:
    print(f"网络错误: {e}")
except ccxt.ExchangeError as e:
    print(f"交易所错误: {e}")
except Exception as e:
    print(f"未知错误: {e}")
