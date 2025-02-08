from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = None
Base = None
session = None

def InitDB(conf):
    global engin, Base, session
    # 创建数据库引擎（使用SQLite3数据库）
    engine = create_engine(conf["DB"]["db_path"], echo=True)
 
    # 创建基础模型
    Base = declarative_base()
    # 创建所有表
    
    class Market(Base):
        __tablename__ = 'markets'

        id = Column(Integer, primary_key=True)
        side = Column(String, nullable=False) # buy/sell 交易方向
        status = Column(String, nullable=False) # 订单状态
        order_id = Column(String, nullable=False) # 订单id
        price = Column(Float, nullable=False) #交易价格
        deleted_at = Column(DateTime, nullable=True)


    Base.metadata.create_all(engine)
 
    # 创建会话
    Session = sessionmaker(bind=engine)
    session = Session()


