import time
import traceback

import ccxt
import pandas as pd
import talib

from sdk import binance
from models import markets
from models.base import session, Market
from utils import thread, queue

book_queues = queue.FixedSizeQueue(10)

T = {
    "up": 0.0,
    "low": 0.0,
    "do_trade": False,
    "do_thread": False,
    "queues": book_queues,
    "side": "",
    "sell_price": 0.0,
    "stop_price": 0.0,
    "handicap": 0,
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
        T["queues"].enqueue(calculate_order_ratio(exchange, symbol, depth=10))

        if T["queues"].queue.__len__() >= 10:
            do_trade, side = book_decision(exchange, symbol, T["queues"].queue)
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
            # NOTE(tracy), 当前如果有订单需要卖出就不在进行买入，但这样不利于充分交易；当前保持现状，后续按需优化
            print(f"当前存在需要交易订单: {order.order_id}, T: {T}")
            if len(open_orders) == 0 :
                if order.side == "BUY":
                    if c_price <= T["stop_price"] and T["handicap"] <= 0:
                        sell_order, ret = binance.create_sell_limit_order(exchange, symbol, order.sell_amount, (c_price - 1), order.order_id)
                        if ret and not T["do_thread"]:
                            print(f"卖出: {order.order_id}, T: {T}")
                            thread.do_thread(check_order, (exchange, sell_order["orderId"], symbol, order.sell_amount, True))

                    if T["handicap"] < 0:
                        sell_order, ret = binance.create_sell_limit_order(exchange, symbol, order.sell_amount, (c_price - 1), order.order_id)
                        if ret and not T["do_thread"]:
                            print(f"卖出: {order.order_id}, T: {T}")
                            thread.do_thread(check_order, (exchange, sell_order["orderId"], symbol, order.sell_amount, True))

                    if c_price >= T["sell_price"] and T["handicap"] > 0:
                        T["stop_price"] = c_price
                        T["sell_price"] = c_price * 1.005
                        print(f"继续持有: {order.order_id}, T: {T}")


        if len(open_orders) == 0 and len(closed_orders) == 0 and T["do_trade"] and T["handicap"] > 0:
            buy_price = c_price + 1.0
            T["stop_price"] = buy_price * 0.99
            T["sell_price"] = buy_price * 1.005

            buy_order, ret = binance.create_buy_limit_order(exchange, symbol, 0.0001, buy_price, T["sell_price"])
            if ret and not T["do_thread"]:
                thread.do_thread(check_order, (exchange, buy_order["orderId"], symbol, 0.0001, False))

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
                        thread.do_thread(check_order, (exchange, open_order.order_id, symbol, 0.0001, False))
                    else:
                        thread.do_thread(check_order, (exchange, open_order.order_id, symbol, 0.0001, True))

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
                                
                            markets.delete_order(session, open_order.order_id)
                            return
                        
                        buy_order, ret = binance.create_buy_limit_order(exchange, symbol, 0.0001, (c_price + 1), T["sell_price"])
                        if ret and not T["do_thread"]:
                            thread.do_thread(check_order, (exchange, buy_order["orderId"], symbol, 0.0001, False))

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
                    if T["up"] != open_order.sell_price:

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

                        sell_order, ret = binance.create_sell_limit_order(exchange, symbol, open_order.sell_amount, (c_price - 1), open_order.peer_order_id)
                        if ret and not T["do_thread"]:
                            thread.do_thread(check_order, (exchange, sell_order["orderId"], symbol, open_order.sell_amount, True))
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

            if order["status"]  == "closed" and order["status"] == "FILLED":
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
                print("Order did not complete: {order}")
                markets.update_market_order(session, order_id, "failed")
                T["do_thread"] = False
                return

            print(f"Check order status, symbol: {symbol}, order id: {order_id}, order: {order}, amount: {amount}")

            time.sleep(2) # 存在限速问题，我们先将间隔定位2s

        except Exception as e:
            raise e


def book_decision(exchange, symbol, queue):
    count = 0

    m, m_signal, m_hist = macd(exchange, symbol)
    if not m or not m_hist or not m_hist:
        return False, ""

    #if m[99] < m[98] and m_hist[99] < m_hist[98]:
    #    return True, "down"

    if m_hist[99] > m_hist[98]:
        for i in range(10):
            print(f"m_hist: {m_hist[99]}, m_hist: {m_hist[98]}, queue: {queue.__getitem__(i)}, count: {count}")
            if float(queue.__getitem__(i)) > 0.6:
                count = count + 1
        
        if count >= 7:
            if T["handicap"] <= 5:
                T["handicap"] = T["handicap"] + 1
                return True, "up"
        else:
            if T["handicap"] >= -5:
                T["handicap"] = T["handicap"] - 1

    return False, ""



def macd(exchange, symbol, timefram = "15m", limit = 100):

    ohlcv = binance.fetch_k(exchange, symbol, timefram, limit)
    
    if ohlcv:
        # 将 K 线数据转换为 DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')  # 转换时间戳
        
        # 计算 MACD 指标
        df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(
            df['close'], fastperiod=12, slowperiod=26, signalperiod=9
        )

        macd = df["macd"][-10:].to_dict()
        macd_signal = df["macd_signal"][-10:].to_dict() # MACD 线的 9 日 EMA，用于生成交易信号。
        macd_hist = df["macd_hist"][-10:].to_dict() # MACD 线与信号线的差值，用于反映市场动量的变化。

        return macd, macd_signal, macd_hist 

    else:
        return None, None, None


def calculate_order_ratio(exchange, symbol, depth=10):
    order_book = binance.get_order_book(exchange, symbol)

    if order_book:
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
    else:
        return 0.0
