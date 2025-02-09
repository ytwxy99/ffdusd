from config.yml import CONF
from utils import pt
from trade.strategy import fdusd as fdd
from trade import base
from models import base as db
from models import markets

def main():
    try:
        pt.Pinit()
        base.init_trade(CONF, True)
        db.migrate()
        print(markets.get_all_markets(db.session))
        #fdd.do(base.exchange, base.SYMBOL)
    except Exception as e:
        print(e)
        exit(1)

if __name__ == "__main__":
    main()
