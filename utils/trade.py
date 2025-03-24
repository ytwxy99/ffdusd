import talib
import pandas as pd

def do_macd(exchange, symbol, binance, timefram="15m", limit=100):
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
        macd_signal = df["macd_signal"][-10:].to_dict()  # MACD 线的 9 日 EMA，用于生成交易信号。
        macd_hist = df["macd_hist"][-10:].to_dict()  # MACD 线与信号线的差值，用于反映市场动量的变化。

        return macd, macd_signal, macd_hist

    else:
        return None, None, None


def calculate_order_ratio(exchange, symbol, binance, depth=10):
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