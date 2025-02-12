import time
from sdk import binance
from models import markets
from models.base import session, Market

T = {
    "up": 0.0,
    "low": 0.0,
    "up_times": 0,
    "low_times": 0,
    "loop": False,
}

def do(exchange, symbol):
    # 所有开始前都需要把挂单都撤销
    cancel_all_orders(exchange, symbol)
    while True:
        c_price = float(binance.fetch_current_price(exchange, symbol))
        decision_make(exchange, c_price, symbol)
        time.sleep(1)


def decision_make(exchange, c_price, symbol):
    global T
    #orders = binance.fetch_open_orders(exchange, symbol)
    open_orders = markets.get_all_open_orders(session)

    if T["up"] == 0.0 and T["low"] == 0.0:
        T["up"] = c_price
        T["low"] = c_price
    
    if c_price > T["up"]:
        T["up"] = c_price
        T["up_times"] = 0
        T["loop"] = False

    if c_price < T["low"]:
        T["low"] = c_price
        T["low_times"] = 0
        T["loop"] = False

    if c_price == T["up"] and c_price != T["low"]:
        T["up_times"] = T["up_times"] + 1

    if c_price == T["low"] and c_price != T["up"]:
        T["low_times"] = T["low_times"] + 1

    if T["up_times"] >= 3 and T["low_times"] >= 3:
        # 如果已买入，则需要用"up" 加个挂单卖出
        # return True  
        if len(open_orders) == 0 and not T["loop"]:
            # 如果没有挂单，需要用"low" 价格挂单买入
            buy_order, ret = binance.cate_buy_limit_order(exchange, symbol, 6, T["low"], T["up"])
            if ret:
                T["loop"] = True
                #TODO(tracy), 这里需要个线程来跟踪订单交易情况，并最终更新order订单记录

        else:
            # 此逻辑处理已有挂单情况下，具体处理情况如下：
            # 1. 当买入价格比最新价格高时，则撤单用最新低价挂单买入。
            # 2. 当order订单记录卖出加个比最新低时候，是否需要撤单重新高价挂单卖出这里需要考虑排队问题，当前
            #    就按照撤单，用最新高价来卖出；
            # 3. 当买入价格比最新价格低时，是否需要撤单重新用最新价格买入这里需要靠谱排队问题，当前就按照撤单
            #    用最新高价来买入；
            if T["loop"]:
                # 已下单买入，则不进行操作
                return True

            for order in open_orders:
                od = order["info"]
                if not T["loop"] and od["side"] == "BUY":
                    # 如果有买单且第一次触发这个条件时候，需要撤销重新用"low" 价格买入
                    if not binance.cancel_order(exchange, symbol, od["orderId"]):
                        T["loop"] = True
                    
                    binance.create_buy_limit_order(exchange, symbol, 6, T["low"])

                elif not T["loop"] and od["side"] == "SELL":
                    # 如果有卖单且第一次触发这个条件时候，需要撤销重新用"up" 价格卖出
                    if not binance.cancel_order(exchange, symbol, od["orderId"]):
                        T["loop"] = True
                    
                    binance.create_buy_limit_order(exchange, symbol, 6, T["up"])


# 撤销所有挂单
def cancel_all_orders(exchange, symbol):
    try:
        orders = binance.fetch_open_orders(exchange, symbol)
        for order in orders:
            binance.cancel_order(exchange, symbol, order["info"]["orderId"])
    except Exception as e:
        print(f"cancel_all_orders {symbol} failed: {e}")
