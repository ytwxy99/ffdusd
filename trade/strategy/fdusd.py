import time
from sdk import binance

T = {
    "up": 0.0,
    "low": 0.0,
    "up_times": 0,
    "low_times": 0,
    "loop": False,
}

def do(exchange, symbol):
    while True:
        c_price = float(binance.fetch_current_price(exchange, symbol))
        print(c_price)
        time.sleep(1)


def decision_make(c_price):
    global T
    orders = binance.fetch_open_orders(exchange, symbol)

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
        print(f"Current price map of {symbol}: {T}")

    if c_price == T["low"] and c_price != T["up"]:
        T["low_times"] = T["low_times"] + 1
        print(f"Current price map of {symbol}: {T}")


    if T["up_times"] >= 3 and T["low_times"] >= 3:
        # 如果已买入，则需要用"up" 加个挂单卖出
        # return True  
        if len(orders) == 0:
            # 如果没有挂单，需要用"low" 价格挂单买入
            binance.create_buy_limit_order(exchange, symbol, 6, T["up"])
        else:
            if T["loop"]:
                return True

            for order in orders:
                od = order[info]
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

