import os
import uuid
import datetime
import sqlalchemy as sa
from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text,
    Unicode,
    UnicodeText,
    Table,
    ForeignKey,
    String,
    DateTime,
    )

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    backref
    )

from zope.sqlalchemy import ZopeTransactionExtension

DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql:///scatterpeas1'
)

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    first = Column(Unicode(50))
    last = Column(Unicode(50))
    username = Column(Unicode(50), nullable=False)
    password = Column(Unicode(60), nullable=False)
    dflt_medium = Column(Unicode(5), default=u'email', nullable=False)
    timezone = Column(
        Unicode(50),
        default=u'America/Los_Angeles',
        nullable=False
    )

    aliases = relationship('Alias', order_by='Alias.id', backref=backref('users', order_by=id))
    # reminders = relationship(
    #     'Reminder',
    #     order_by='Reminder.id',
    #     backref='users'
    # )

    def __repr__(self):
        return "<User(first='%s', last='%s', username='%s', dflt_medium='%s')>" % (self.first, self.last, self.username, self.dflt_medium)


class Alias(Base):
    __tablename__ = 'aliases'
    id = Column(Integer, primary_key=True, autoincrement=True)
    alias = Column(Unicode(100), default=u'ME', nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    contact = Column(Unicode(75))
    contact_state = Column(Integer, default=0)

    uuids = relationship('UUID', order_by='UUID.id', backref=backref('aliases', order_by=id))
    # reminders = relationship(
    #     'Reminder',
    #     order_by='Reminder.id',
    #     backref='aliases'
    # )

    def __repr__(self):
        return "<Alias(name='%s', contact='%s', c_state='%s', user_id='%s')>" %  (self.alias, self.contact, self.contact, self.user_id)


class UUID(Base):
    __tablename__ = 'uuids'
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(Unicode(36), nullable=False, default=uuid.uuid4)
    alias_id = Column(Integer, ForeignKey('aliases.id'), nullable=False)
    medium = Column(Unicode(5), default=u'email', nullable=False)
    created = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        nullable=False)

    def __repr__(self):
        return "<UUID(uuid='%s', medium='%s', created='%s', alias_id='%s')>" %  (self.uuid, self.medium, self.created, self.alias_id)


if __name__ == '__main__':
    foo = User(first='foo', last='bar', username='foobar', password='asdf')
    biz = User(first='biz', last='baz', username='bizbaz', password='1qaz')
    engine = sa.create_engine(DATABASE_URL, echo=True)
    Base.metadata.create_all(engine)
    DBSession.configure(bind=engine)
