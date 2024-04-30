import datetime
import sqlalchemy as sa
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Result(SqlAlchemyBase):
    __tablename__ = 'results'

    id = sa.Column(sa.Integer,
                   primary_key=True, autoincrement=True)
    analyze_answer = sa.Column(sa.String, nullable=True)
    date = sa.Column(sa.DateTime, default=datetime.datetime.now)

    user_id = sa.Column(sa.Integer,
                        sa.ForeignKey("users.id"))
    user = orm.relationship('User')
