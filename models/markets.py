from datetime import datetime
from models import base

def create_market(session, market):
    session.add(market)
    session.commit()


def fetch_market(session, order_id):
    return session.query(base.Market).filter_by(order_id=order_id).filter(base.Market.deleted_at.is_(None)).first()


def update_market_status(session, order_id, status):
    market = session.query(base.Market).filter_by(order_id=order_id).first()
    market.status = status
    session.commit()
    

def delete_market(session, order_id):
    to_delete = session.query(base.Market).filter_by(order_id=order_id).first()
    if to_delete:
        to_delete.deleted_at = datetime.utcnow()
        session.commit()


def get_all_markets(session):
    return session.query(base.Market).filter(base.Market.deleted_at.is_(None)).all()
