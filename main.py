from config import yml
from utils import pt
from trade import base
from trade.strategy import fdusd as fdd

def main():
    try:
        pt.Pinit()
        yml.InitConf("/Users/bytedance/Documents/project/ffdusd/etc/ffdusd/ffdusd.yml")
        base.init_trade(yml.CONF, True)
        fdd.do(base.exchange, base.SYMBOL)
    except Exception as e:
        print(e)
        exit(1)

if __name__ == "__main__":
    main()
