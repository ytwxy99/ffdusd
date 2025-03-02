import ccxt
import pandas as pd
import talib

# 初始化交易所
exchange = ccxt.binance()  # 以币安为例

# 设置交易对和时间周期
symbol = 'BTC/USDT'
timeframe = '15m'  # 15 分钟 K 线

# 获取历史 K 线数据
limit = 100  # 获取最近的 100 根 K 线
ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

# 将 K 线数据转换为 DataFrame
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')  # 转换时间戳

# 计算 MACD 指标
df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(
    df['close'], fastperiod=12, slowperiod=26, signalperiod=9
)

# 打印结果
print(df[['timestamp', 'close', 'macd', 'macd_signal', 'macd_hist']].tail())
