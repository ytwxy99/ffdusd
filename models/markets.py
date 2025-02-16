from datetime import datetime
from models.base import Market 
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import and_, or_



def create_order(session, market):
    session.add(market)
    session.commit()


def fetch_order(session, order_id):
    return session.query(Market).filter_by(order_id=order_id).filter(Market.deleted_at.is_(None)).first()


def update_market_order(session, order_id, status):
    market = session.query(Market).filter_by(order_id=order_id).first()
    market.status = status
    session.commit()
    

def delete_order(session, order_id):
    to_delete = session.query(Market).filter_by(order_id=order_id).first()
    if to_delete:
        to_delete.deleted_at = datetime.utcnow()
        session.commit()


# 获取所有已成交的订单
def get_all_closed_orders(session):
    return session.query(Market).filter(and_(Market.deleted_at.is_(None), Market.status == "closed")).all()


def get_all_open_orders(session):
    return session.query(Market).filter(and_(Market.deleted_at.is_(None), or_(Market.status != "closed", Market.status != "canceled"))).all()

# 获取peer的订单
def fetch_peer_order(session, order_id):
    return session.query(Market).filter(and_(Market.deleted_at.is_(None), Market.status == "closed", Market.peer_order_id)).all()
