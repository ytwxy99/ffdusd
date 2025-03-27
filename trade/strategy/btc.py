import time
import traceback

import ccxt

from sdk import binance
from models import markets
from models.base import session, Market
from utils import thread, queue
from utils.trade import do_macd, calculate_order_ratio

book_queues = queue.FixedSizeQueue(10)

T = {
    "up": 0.0,
    "low": 0.0,
    "do_trade": False,
    "do_thread": False,
    "queues": book_queues,
    "side": "",
    "close_price": 0.0,
    "stop_price": 0.0,
    "handicap": 0,
    "amount": 0.0,
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
        T["queues"].enqueue(calculate_order_ratio(exchange, symbol, binance))

        if T["queues"].queue.__len__() >= 10:
            do_trade, side, macd, is_macd_up = book_decision(exchange, symbol, T["queues"].queue)
            print(f"交易决策: {do_trade}, side: {side}, macd: {macd}, c_price: {c_price}")
            if do_trade:
                T["do_trade"] = do_trade
                T["side"] = side
        
        if T["up"] == 0.0 and T["low"] == 0.0:
            T["up"] = c_price
            T["low"] = c_price
        
        if c_price > T["up"]:
            T["low"] = T["up"]
            T["up"] = c_price

        if c_price < T["low"]:
            T["up"] = T["low"]
            T["low"] = c_price

        # 卖出
        closed_orders = markets.get_all_closed_orders(session)
        for order in closed_orders:
            print(f"当前存在需要交易订单: {order.order_id}, T: {T}, buy_price: {order.price}, c_price: {c_price}, increase: {(c_price-order.price)/order.price*100}")
            if len(open_orders) == 0 :
                if order.side == "BUY":
                    if c_price <= T["stop_price"]:
                        sell_order, ret = binance.close_position(exchange, symbol, order.close_amount, (c_price - 1), order.order_id, "buy")
                        if ret and not T["do_thread"]:
                            print(f"卖出: {order.order_id}, T: {T}")
                            thread.do_thread(check_order, (exchange, sell_order["orderId"], symbol, order.close_amount, True))

                    if c_price >= T["close_price"]:
                        T["stop_price"] = c_price * 0.999
                        T["close_price"] = c_price * 1.003
                        print(f"更新目标, 继续持有: {order.order_id}, T: {T}")


        if len(open_orders) == 0 and len(closed_orders) == 0 and T["do_trade"] and T["handicap"] > 0:
            open_price = c_price + 1.0
            T["stop_price"] = open_price * 0.999
            T["close_price"] = open_price * 1.003

            amount = binance.get_max_amount(exchange, symbol, 3, c_price, T["side"])
            print(f"最多可用杠杆数量: {amount}, 方向: {side}")
            if amount == 0:
                return
            else:
                T["amount"] = amount

            o_order, ret = binance.open_position(exchange, symbol, T["side"], T["amount"], open_price, T["close_price"], leverage=3)
            if ret and not T["do_thread"]:
                thread.do_thread(check_order, (exchange, o_order["orderId"], symbol, T["amount"], False))

        elif len(open_orders) != 0:

            for open_order in open_orders:
                if not T["do_thread"]:
                    if open_order.side == "BUY":
                        thread.do_thread(check_order, (exchange, open_order.order_id, symbol, T["amount"], False))
                    else:
                        thread.do_thread(check_order, (exchange, open_order.order_id, symbol, T["amount"], True))

                print(f"挂单检测，T：{T}, 预期成交价格: {open_order.price}")
                if open_order.side == "BUY":
                    # 如果有买单且第一次触发这个条件时候，需要撤销重新用"low" 价格买入
                    if T["up"] != open_order.price and T["handicap"] > 0:
                        print(f"价格波动，进行已有挂单检测: {open_order.__dict__}, T: {T}")
                        if binance.cancel_order(exchange, symbol, open_order.order_id): 
                            markets.delete_order(session, open_order.order_id)
                        else:
                            retry = 0
                            while True:
                                time.sleep(5)
                                if retry >= 3:
                                    break

                                if binance.cancel_order(exchange, symbol, open_order.order_id):
                                    markets.delete_order(session, open_order.order_id)
                                    break

                                retry = retry + 1
                                
                            return
                        
                        buy_order, ret = binance.create_buy_limit_order(exchange, symbol, T["amount"], (c_price + 1), T["close_price"])
                        if ret and not T["do_thread"]:
                            thread.do_thread(check_order, (exchange, buy_order["orderId"], symbol, T["amount"], False))

                    if T["handicap"] < 0:
                        print(f"买点消失，取消交易:{open_order.__dict__}, T: {T}")
                        if binance.cancel_order(exchange, symbol, open_order.order_id):
                            markets.delete_order(session, open_order.order_id)
                        else:
                            retry = 0
                            while True:
                                time.sleep(5)
                                if retry >= 3:
                                    break

                                if binance.cancel_order(exchange, symbol, open_order.order_id):
                                    markets.delete_order(session, open_order.order_id)
                                    break

                                retry = retry + 1
                                
                            markets.delete_order(session, open_order.order_id)
                            return


                if open_order.side == "SELL":
                    # 如果有卖单且第一次触发这个条件时候，需要撤销重新用"up" 价格卖出
                    if T["up"] != open_order.close_price:

                        print(f"价格波动，进行已有挂单检测: {open_order.__dict__}, T: {T}")
                        if binance.cancel_order(exchange, symbol, open_order.order_id):
                            markets.delete_order(session, open_order.order_id)
                        else:
                            retry = 0
                            while True:
                                time.sleep(5)
                                if retry >= 3:
                                    break

                                if binance.cancel_order(exchange, symbol, open_order.order_id):
                                    markets.delete_order(session, open_order.order_id)
                                    break

                                retry = retry + 1
                                
                            markets.delete_order(session, open_order.order_id)
                            return
                        
                        if T["handicap"] > 0:
                            return 

                        sell_order, ret = binance.create_sell_limit_order(exchange, symbol, open_order.close_amount, (c_price - 1), open_order.peer_order_id)
                        if ret and not T["do_thread"]:
                            thread.do_thread(check_order, (exchange, sell_order["orderId"], symbol, open_order.close_amount, True))
                    else:
                           
                        if T["handicap"] > 0:
                            print(f"预期上涨，撤销卖单: {open_order.__dict__}, T: {T}")
                            if binance.cancel_order(exchange, symbol, open_order.order_id):
                                markets.delete_order(session, open_order.order_id)
                            else:
                                return

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

            if order["status"]  == "closed" or order["status"] == "FILLED":
                markets.update_market_order(session, order_id, "closed")
                # NOTE(tracy), delete peer order record when sell order has been finished.
                sell_order = markets.fetch_order(session, order_id)
                if close_peer:
                    markets.delete_order(session, order_id)
                    markets.delete_order(session, sell_order.peer_order_id)
                else:
                    sell_account = binance.fetch_sell_account(exchange)
                    markets.update_market_order(session, order_id, "closed", sell_account.real)

                print(f"Order completed successfully: {order}")
                T["do_thread"] = False
                return

            elif order["status"] == "canceled" or order["status"] == "expired":
                print(f"Order did not complete: {order}")
                markets.update_market_order(session, order_id, "failed")
                T["do_thread"] = False
                return

            print(f"Check order status, symbol: {symbol}, order id: {order_id}, order: {order}, amount: {amount}")

            time.sleep(2) # 存在限速问题，我们先将间隔定位2s

        except Exception as e:
            raise e


def book_decision(exchange, symbol, queue):
    count = 0

    m, m_signal, m_hist = do_macd(exchange, symbol, binance)
    if not m or not m_hist or not m_hist:
        return False, "", 0, False

    # if m[99] <= 0 and m_hist[99] < m_hist[98]:
    #     for i in range(10):
    #         if float(queue.__getitem__(i)) < 0.4:
    #             count = count + 1
    #
    #     if count >= 7:
    #         if T["handicap"] <= 5:
    #             T["handicap"] = T["handicap"] + 1
    #             return True, "sell", m[99]
    #     else:
    #         if T["handicap"] >= -5:
    #             T["handicap"] = T["handicap"] - 1
    #
    #     return False, "sell", m[99]

    if m_hist[99] > m_hist[98] and m[99] > m[98]:
        for i in range(10):
            if float(queue.__getitem__(i)) > 0.6:
                count = count + 1
        
        if count >= 7:
            if T["handicap"] <= 5:
                T["handicap"] = T["handicap"] + 1
                return True, "buy", m[99], m[99] > m[98]
        else:
            if T["handicap"] >= -5:
                T["handicap"] = T["handicap"] - 1

    return False, "buy", m[99], m[99] > m[98]
