import datetime

from sqlalchemy import *
from werkzeug.security import generate_password_hash, check_password_hash

from .db_session import SqlAlchemyBase, create_session


class User(SqlAlchemyBase):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    melon_id = Column(String, unique=True)
    discord_id = Column(Integer, unique=True)
    balance = Column(Integer, default=0)

    last_action = Column(DateTime, default=datetime.datetime.now())
    hashed_password = Column(String)

    def add_money(self, amount: float | int, comment: str =''):
        self.update_action()
        session = create_session()
        record = Operation(self.id, amount, comment)
        session.add(record)
        session.commit()
        self.balance += int(amount)

    def set_melon_id(self, new_id: str):
        self.update_action()
        self.melon_id = new_id

    def update_action(self):
        self.last_action = datetime.datetime.now()

    def set_password(self, password: str):
        self.update_action()
        self.hashed_password = generate_password_hash(password)
        self.last_action = datetime.datetime.now()

    def check_password(self, password: str):
        return check_password_hash(self.hashed_password, password)

    def __repr__(self):
        return f'{self.id}-{self.melon_id}'


class Operation(SqlAlchemyBase):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(Integer, ForeignKey("users.id"))
    amount = Column(Integer)
    comment = Column(String)

    def __init__(self, user: Column[int], amount: int, comment: str = ''):
        self.user = user
        self.amount = amount
        self.comment = comment
