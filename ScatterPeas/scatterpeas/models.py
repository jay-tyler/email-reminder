import os
import sqlalchemy as sa
from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text,
    Unicode,
    UnicodeText,
    )

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

from zope.sqlalchemy import ZopeTransactionExtension

DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql:///scatterPeas1'
)

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    first = Column(Unicode(50))
    last = Column(Unicode(50))
    username = Column(Unicode(50), nullable=False)
    password = Column(Unicode(50), nullable=False)
    dflt_medium = Column(Unicode(5), default='email')

    def __repr__(self):
        return "<User(first=' %s', last=' %s', username=' %s', dflt_medium=' %s')>" % (self.first, self.last, self.username, self.dflt_medium)





def init_db():
    engine = sa.create_engine(DATABASE_URL, echo=True)
    Base.metadata.create_all(engine)
    DBSession.configure(bind=engine)
