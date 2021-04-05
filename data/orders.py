import sqlalchemy
from .db_session import SqlAlchemyBase


class Order(SqlAlchemyBase):
    __tablename__ = 'orders'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, index=True)
    order = sqlalchemy.Column(sqlalchemy.String, nullable=False)
