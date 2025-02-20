from config.yml import CONF as conf
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


engine = create_engine(conf["DB"]["db_path"], echo=False)
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()


class Market(Base):
    __tablename__ = 'markets'

    id = Column(Integer, primary_key=True)
    side = Column(String, nullable=False) # buy/sell 交易方向
    status = Column(String, nullable=False) # 订单状态
    order_id = Column(String, nullable=False) # 订单id
    peer_order_id = Column(String, nullable=True) # 订单id
    price = Column(Float, nullable=False) # 交易价格
    sell_price = Column(Float, nullable=False) # 卖出交易价格
    deleted_at = Column(DateTime, nullable=True)

def migrate():
    Base.metadata.create_all(engine)

