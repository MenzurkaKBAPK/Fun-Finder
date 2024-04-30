import sqlalchemy as sa
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = sa.Column(sa.Integer,
                   primary_key=True, autoincrement=True)
    user_id = sa.Column(sa.String, nullable=True)

    result = orm.relationship("Result", back_populates='user')
