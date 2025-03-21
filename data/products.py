import sqlalchemy

from .db_session import SqlAlchemyBase


class Product(SqlAlchemyBase):
    __tablename__ = 'products'

    id = sqlalchemy.Column(sqlalchemy.Integer, index=True,
                           primary_key=True, autoincrement=True)
    image = sqlalchemy.Column(sqlalchemy.String, nullable=True, default="default.png")
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False, default="")
    price = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, default=0)
    description = sqlalchemy.Column(sqlalchemy.Text, default="Описание отсутствует")
