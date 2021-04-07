import sqlalchemy
from .db_session import SqlAlchemyBase


class Order(SqlAlchemyBase):
    __tablename__ = 'orders'

    id = sqlalchemy.Column(sqlalchemy.Integer, autoincrement=True, primary_key=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, index=True)
    order = sqlalchemy.Column(sqlalchemy.String, default="")
    total_price = sqlalchemy.Column(sqlalchemy.String, default="0")
