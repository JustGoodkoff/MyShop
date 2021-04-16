import sqlalchemy

from .db_session import SqlAlchemyBase


class UnregOrder(SqlAlchemyBase):
    __tablename__ = 'unreg_orders'

    id = sqlalchemy.Column(sqlalchemy.Integer, autoincrement=True, primary_key=True)
    user_phone_number = sqlalchemy.Column(sqlalchemy.Integer)
    address = sqlalchemy.Column(sqlalchemy.String, default="")
    order = sqlalchemy.Column(sqlalchemy.String, default="")
    total_price = sqlalchemy.Column(sqlalchemy.Integer, default=0)
