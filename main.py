from config.yml import CONF
from utils import pt
from trade.strategy import btc
from trade import base
from models import base as db

def main():
    try:
        pt.Pinit()
        base.init_trade(CONF, True)
        db.migrate()
        btc.do(base.exchange, CONF["SYMBOL"]["peer"])
    except Exception as e:
        print(e)
        exit(1)

if __name__ == "__main__":
    main()
