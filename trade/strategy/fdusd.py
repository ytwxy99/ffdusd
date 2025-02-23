import time
import traceback

from sdk import binance
from models import markets
from models.base import session, Market
from utils import thread

T = {
    "up": 0.0,
    "low": 0.0,
    "up_times": 0,
    "low_times": 0,
    "do_thread": False,
}

def do(exchange, symbol):
    # 所有开始前都需要把挂单都撤销
    #cancel_all_orders(exchange, symbol)
    while True:
        c_price = binance.fetch_current_price(exchange, symbol)
        if c_price:
            decision_make(exchange, float(c_price), symbol)
            time.sleep(1)

def decision_make(exchange, c_price, symbol):
    try:
        global T
        open_orders = markets.get_all_open_orders(session)

        print(f"do decision, open_order: {open_orders}")

        if T["up"] == 0.0 and T["low"] == 0.0:
            T["up"] = c_price
            T["low"] = c_price
        
        if c_price > T["up"]:
            T["low"] = T["up"]
            T["up"] = c_price
            T["up_times"] = 0
            T["low_times"] = 0

        if c_price < T["low"]:
            T["up"] = T["low"]
            T["low"] = c_price
            T["up_times"] = 0
            T["low_times"] = 0

        #if c_price == T["up"] and c_price != T["low"]:
        #    T["up_times"] = T["up_times"] + 1

        #if c_price == T["low"] and c_price != T["up"]:
        #    T["low_times"] = T["low_times"] + 1

        #if T["up_times"] >= 3 and T["low_times"] >= 3:
        if book_decision(exchange, symbol):
            # 如果已买入, 则需要用"up" 加个挂单卖出
            closed_orders = markets.get_all_closed_orders(session)
            for order in closed_orders:
                # NOTE(tracy), 当前如果有订单需要卖出就不在进行买入，但这样不利于充分交易；当前保持现状，后续按需优化
                print(f"当前存在需要交易订单: {order.order_id}, T: {T}")
                if len(open_orders) == 0 :
                    if order.side == "BUY":
                        # 这里认为均值会回归，故低于buy单记录的卖出价也等待均值回归后卖出
                        if T["low"] >= order.sell_price:
                            do_sell_price = T["low"]
                        else:
                            do_sell_price = order.sell_price

                        sell_order, ret = binance.create_sell_limit_order(exchange, symbol, 6, do_sell_price, order.order_id)
                        if ret and not T["do_thread"]:
                            thread.do_thread(check_order, (exchange, sell_order["orderId"], symbol, 6, True))

            if len(open_orders) == 0 and len(closed_orders) == 0:
                buy_order, ret = binance.create_buy_limit_order(exchange, symbol, 6, T["low"], T["up"])
                if ret and not T["do_thread"]:
                    thread.do_thread(check_order, (exchange, buy_order["orderId"], symbol, 6, False))

            elif len(open_orders) != 0:
                # 此逻辑处理已有挂单情况下，具体处理情况如下：
                # 1. 当买入价格比最新low价格高时，则撤单用最新低价挂单买入。
                # 2. 当order订单记录卖出价格比最新low低时候，是否需要撤单重新高价挂单卖出这里需要考虑排队问题，当前
                #    就按照撤单，用最新高价来卖出；
                # 3. 当买入价格比最新low价格低时，是否需要撤单重新用最新价格买入这里需要靠谱排队问题，当前就按照撤单
                #    用最新高价来买入;
                
                for open_order in open_orders:

                    if not T["do_thread"]:
                        if open_order.side == "BUY":
                            thread.do_thread(check_order, (exchange, open_order.order_id, symbol, 6, False))
                        else:
                            thread.do_thread(check_order, (exchange, open_order.order_id, symbol, 6, True))

                    print(f"挂单检测，T：{T}, 预期成交价格: {open_order.price}")
                    if open_order.side == "BUY":
                        # 如果有买单且第一次触发这个条件时候，需要撤销重新用"low" 价格买入
                        if T["low"] < open_order.price:
                            print(f"价格波动，进行已有挂单检测: {open_order.__dict__}, T: {T}")
                            if binance.cancel_order(exchange, symbol, open_order.order_id):
                                markets.delete_order(session, open_order.order_id)
                            else:
                                return
                            
                            buy_order, ret = binance.create_buy_limit_order(exchange, symbol, 6, T["low"], T["up"])
                            if ret and not T["do_thread"]:
                                thread.do_thread(check_order, (exchange, buy_order["orderId"], symbol, 6, False))

                    if open_order.side == "BUY":
                        if T["low"] > open_order.price:
                            print(f"价格波动，进行已有挂单检测: {open_order.__dict__}, T: {T}")
                            if binance.cancel_order(exchange, symbol, open_order.order_id):
                                markets.delete_order(session, open_order.order_id)
                            else:
                                return

                            buy_order, ret = binance.create_buy_limit_order(exchange, symbol, 6, T["low"], T["up"])
                            if ret and not T["do_thread"]:
                                thread.do_thread(check_order, (exchange, buy_order["orderId"], symbol, 6, False))

                    if open_order.side == "SELL":
                        # 如果有卖单且第一次触发这个条件时候，需要撤销重新用"up" 价格卖出
                        if T["up"] != open_order.sell_price:
                            print(f"价格波动，进行已有挂单检测: {open_order.__dict__}, T: {T}")
                            if binance.cancel_order(exchange, symbol, open_order.order_id):
                                markets.delete_order(session, open_order.order_id)
                            else:
                                return
                            
                            sell_order, ret = binance.create_sell_limit_order(exchange, symbol, 6, T["up"], open_order.peer_order_id)
                            if ret and not T["do_thread"]:
                                thread.do_thread(check_order, (exchange, sell_order["orderId"], symbol, 6, True))

    except Exception as e :
        traceback.print_exc()


# 撤销所有挂单
def cancel_all_orders(exchange, symbol):
    try:
        orders = binance.fetch_open_orders(exchange, symbol)
        for order in orders:
            binance.cancel_order(exchange, symbol, order["info"]["orderId"])
    except Exception as e:
        print(f"cancel_all_orders {symbol} failed: {e}")


def check_order(*order_args):
    global T
    exchange, order_id, symbol, amount, close_peer = order_args

    while True:
        T["do_thread"] = True

        try:
            order = binance.check_order_status(exchange, order_id, symbol)
            if not order:
                print(f"fetch_order failed: {order_id}")
                continue

            if order["status"]  == "closed" and order["filled"] == amount:
                markets.update_market_order(session, order_id, order["status"])
                # NOTE(tracy), delete peer order record when sell order has been finished.
                sell_order = markets.fetch_order(session, order_id)
                if close_peer:
                    markets.delete_order(session, order_id)
                    markets.delete_order(session, sell_order.peer_order_id)
                print(f"Order completed successfully: {order}")
                T["do_thread"] = False
                break

            elif order["status"] == "canceled" or order["status"] == "expired":
                print("Order did not complete: {order}")
                markets.update_market_order(session, order_id, "failed")
                T["do_thread"] = False
                break

            print(f"Check order status, symbol: {symbol}, order id: {order_id}, status: {order['status']}, price: {order['price']}")

            time.sleep(2) # 存在限速问题，我们先将间隔定位2s

        except Exception as e:
            raise e

def book_decision(exchange, symbol):
    books = binance.get_first_order_book(exchange, symbol)
    if books["sell_count"] > 5000 and books["buy_count"] > 5000:
        if books["buy_count"] > books["sell_count"]:
            return True
        else:
            return False

    else:
        return False

