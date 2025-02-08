from db import base
from sqlalchemy import Column, Integer, String, Float


# 定义User模型
class Market(base.Base):
    __tablename__ = 'markets'

    id = Column(Integer, primary_key=True)
    side = Column(String, nullable=False) # buy/sell 交易方向
    status = Column(String, nullable=False) # 订单状态
    order_id = Column(String, nullable=False) # 订单id
    price = Column(Float, nullable=False) #交易价格
    deleted_at = Column(DateTime, nullable=True)
