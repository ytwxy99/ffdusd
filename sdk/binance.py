import ccxt

from models.base import Market, session
from models import markets

# 初始化币安交易所实例
def auth_exchagne_binance(ak, sk, is_enable_rate_limit):
    return ccxt.binance({
        'apiKey': ak,
        'secret': sk, 
        'enableRateLimit': is_enable_rate_limit,  # 启用速率限制
        'options': {
            'defaultType': 'margin',  # 设置为保证金交易模式
            'autoRepay': True,
        }
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
            order_id = order["info"]["orderId"]
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
            order_id = order["info"]["orderId"]
            side = order["info"]["side"]
            status = order["info"]["status"]

            new_order = Market(order_id=order_id, side=side, status=status, sell_price=price, price=price, peer_order_id=peer_order_id, sell_amount=amount)
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


def fetch_k(exchange, symbol, timeframe, limit):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        return ohlcv
    except Exception as e:
        print(f"Error fetching ohlcv failed: {e}")
        return None


def get_order_book(exchange, symbol):
    try:
        order_book = exchange.fetch_order_book(symbol)
        return order_book
    except Exception as e:
        print(f"Error fetching order book failed: {e}")
        return None


def fetch_sell_account(exchange, symbol="BTC"):
    """获取BTC可以使用的所有数量"""
    try:
        balance = exchange.fetch_balance()
        return float(balance[symbol]['free'])

    except Exception as e:
        print(f"Error fetching sell account: {e}")
        raise 


def fetch_buy_btc_amount(exchange):
    try:
        # 获取账户余额
        balance = exchange.fetch_balance()
        usdt_balance = balance['free']['USDT']  # 假设USDT在你的账户中是可用的

        # 获取USDT/BTC交易对的价格
        ticker = exchange.fetch_ticker('BTC/USDT')
        btc_price = ticker['last']  # 使用最新交易价格

        # 计算USDT能够购买的BTC数量
        btc_amount = usdt_balance / btc_price
        print(f"你当前有 {usdt_balance} USDT，可以购买 {btc_amount:.8f} BTC。")

        return btc_amount

    except Exception as e:
        print(f"fetch_buy_btc_amount failed: {e}")
        return 0


def get_max_amount(exchange, symbol, leverage, c_price, side):
    try:
        if side == "buy":
            balance = exchange.fetch_balance(params={'type': 'margin'})
            free_usdt = balance['USDT']['free']

            max_btc_theoretical = (free_usdt * leverage) / c_price

            market_info = exchange.market(symbol)
            max_notional = market_info['limits']['cost']['max']  # 例如 100万USDT
            max_btc_actual = min(max_btc_theoretical, max_notional / c_price)
            adjusted_quantity = exchange.amount_to_precision(symbol, max_btc_actual)

            return adjusted_quantity

        elif side == "sell":
            # 1. 获取逐仓账户余额（使用标准方法）
            params = {
                #'isIsolated': 'TRUE',  # 关键参数：指定逐仓模式
                'symbols': symbol  # 需要指定交易对ID如BTCUSDT
            }
            balance = exchange.fetch_balance(params=params)

            market_info = exchange.market(symbol)
            # 提取BTC可用余额
            btc_free = float(balance['free'].get(market_info['base'], 0))

            # 2. 获取最大可借BTC数量（使用ccxt标准方法）
            max_borrow = exchange.sapi_get_margin_maxborrowable({'asset':  market_info['base']})
            max_borrowable_btc = float(max_borrow['amount'])
            # 4. 计算总可做空量（考虑杠杆）
            # total_shortable = (btc_free + max_borrowable_btc) * leverage
            total_shortable = (btc_free + max_borrowable_btc)
            # 5. 调整精度
            adjusted_quantity = exchange.amount_to_precision(symbol, total_shortable)

            return adjusted_quantity

    except Exception as e:
        print(f"获取杠杆交易做大下单数量错误: {e}")
        return 0


# 杠杆开仓
def open_position(exchange, symbol, side, amount, price, close_price, leverage=3):
    """
        开仓（做多/做空）
        :param side: 'buy'（做多） 或 'sell'（做空）
        :param amount: 买入/卖出数量
        :param leverage: 杠杆倍数
    """
    try:
        order = exchange.create_order(
                symbol=symbol,
                type='limit',
                side=side,
                amount=amount,
                price=price,
                params={
                    'marginMode': 'isolated',  # 隔离保证金模式
                    'sideEffectType': 'AUTO_BORROW_REPAY'
                }
            )

        print(f"Open position created, order: {order}")

        if order:
            order_id = order["info"]["orderId"]
            side = order["info"]["side"]
            status = order["info"]["status"]

            new_order = Market(order_id=order_id, side=side, status=status, close_price=close_price, price=price, close_amount=amount)
            markets.create_order(session, new_order)
            print(f"open postion created, order_id: {order_id}, price: {price}")
            return order["info"], True

    except ccxt.BaseError as e:
        print(f"Error creating buy order: {e}")
        return None, False


# 杠杆平仓
def close_position(exchange, symbol, amount, price, peer_order_id, side):
    try:
        # 获取当前持仓
        position = get_isolated_position(exchange, symbol)
        if not position:
            print("没有持仓可平")
            return

        market = exchange.market(symbol)

        # 计算需要平仓的数量
        if side == 'buy':
            # 平多仓：卖出基础资产 (BTC)
            qty_to_sell = position['base_asset']['free']
            side_type = 'sell'
        elif side == 'sell':
            # 平空仓：买入基础资产 (BTC)
            qty_to_buy = position['base_asset']['borrowed']
            side_type = 'buy'
        else:
            raise ValueError("仓位类型错误，必须是 long 或 short")

        if qty_to_sell <= 0 and qty_to_buy <= 0:
            print("没有持仓可平")
            return

        # 调整数量精度
        adjusted_qty = exchange.amount_to_precision(symbol, qty_to_sell if side == 'buy' else qty_to_buy)
        import pdb;pdb.set_trace()

        # 创建平仓订单（带自动还款）
        params = {
            'marginMode': 'isolated',
            'sideEffectType': 'AUTO_REPAY'  # 关键参数：触发自动还款
        }

        close_order = exchange.create_order(
            symbol=symbol,
            type='limit',
            price=price,
            side=side_type,
            amount=adjusted_qty,
            params=params
        )

        if close_order:
            order_id = close_order["info"]["orderId"]
            side = close_order["info"]["side"]
            status = close_order["info"]["status"]
            new_order = Market(order_id=order_id, side=side, status=status, close_price=price, price=price, peer_order_id=peer_order_id, close_amount=adjusted_qty)
            markets.create_order(session, new_order)
            print(f"Close position created, order_id: {order_id}, price: {price}")
            return close_order["info"], True

    except ccxt.InsufficientFunds as e:
        print(f"平仓失败，资金不足: {e}")
        return None, False
    except ccxt.NetworkError as e:
        print(f"网络错误: {e}")
        return None, False
    except Exception as e:
        print(f"未知错误: {e}")
        return None, False

def get_isolated_position(exchange, symbol):
    """获取逐仓持仓信息"""
    try:
        # 获取杠杆账户资产详情
        params = {'isIsolated': 'TRUE'}
        balance = exchange.fetch_balance(params=params)

        # 提取指定交易对的持仓
        isolated_symbol = symbol.split('/')[0]
        for asset in balance['info']['userAssets']:
            if asset['asset'] == isolated_symbol:
                return {
                    'base_asset': {
                        'free': float(asset['free']),
                        'borrowed': float(asset['borrowed'])
                    },
                }
        return None
    except Exception as e:
        print(f"获取持仓失败: {e}")
        return None