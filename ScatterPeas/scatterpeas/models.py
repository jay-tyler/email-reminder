# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import uuid
from datetime import datetime, timedelta
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
    Boolean
    )

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    backref
    )

from cryptacular.bcrypt import BCRYPTPasswordManager
from zope.sqlalchemy import ZopeTransactionExtension

DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql:///scatterpeas3'
)

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))

Base = declarative_base()

# engine = create_engine(DATABASE_URL, echo=True)
# Session = sessionmaker(bind=engine)
# DBSession = Session()
# engine = create_engine(DATABASE_URL, echo=True)
# Base.metadata.create_all(engine)
# Session = sessionmaker(bind=engine)


# class Reminders(Base):

#     __tablename__ = 'reminders'

#     id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
#     alias_id = Column(Integer, ForeignKey('aliases.id'), nullable=False)
#     # keeps the rrule currently generating jobs
#     rrule_id = Column(Integer, ForeignKey('rrules.id'), nullable=False)
#     title = Column(Unicode(256), nullable=False)
#     text_payload = Column(Unicode(20000))
#     # this might end up just being a link to a static resourc; we will see
#     media_payload = Column(Unicode(256))
#     # rstate is used to to track whether a reminder is still producing jobs
#     # turned to False after execution of last job
#     rstate = Column(Integer)
#     # next_event = Column(DateTime(timezone=True))
#     # child = relationship("", backref=backref("reminders", uselist=False))

#     @classmethod
#     def create(cls, title="", text_payload="", media_payload="",
#                rstate=True, session=None, user_id=0, alias_id=0):
#         if session is None:
#             session = DBSession
#         if title != "" and alias_id != 0:
#             '''Reminder instance is created, but may not potentially have
#             all necessary attributes including rrule_id. It is the parent
#             function's responsibility to provide
#             these.
#             '''
#             instance = cls(title=title,
#                            text_payload=text_payload,
#                            media_payload=media_payload, rstate=rstate)
#             session.add(instance)
#             return instance


# class RRules(Base):
#     """Contains iCal specification rules corresponding to an event. This
#     class is not yet fully implemented, but stands in for future
#     expandability"""
#     __tablename__ = 'rrules'
#     # constrain this to primary key of reminders
#     id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
#     reminder_id = Column(Integer, ForeignKey('reminders.id'))

#     @classmethod
#     def create(cls, reminder_id=0, session=None):
#         if session is None:
#             session = DBSession
#         if reminder_id != 0:
#             instance = cls(reminder_id=reminder_id)
#             session.add(instance)
#             return instance


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    first = Column(Unicode(50))
    last = Column(Unicode(50))
    username = Column(Unicode(50), nullable=False)
    password = Column(String(60), nullable=False)
    # medium state is 1 for email 2 for text
    dflt_medium = Column(Integer, default=1, nullable=False)
    timezone = Column(
        Unicode(50),
        default='America/Los_Angeles',
        nullable=False
    )

    aliases = relationship(
        'Alias',
        order_by='Alias.id',
        backref=backref('users', order_by=id)
    )
    # reminders = relationship(
    #     'Reminders',
    #     order_by='Reminders.id',
    #     backref=backref('users', order_by=id)
    # )

    @classmethod
    def create_user(cls, username, password, first="", last="",
                    dflt_medium=1, timezone='America/Los_Angeles', session=None):
        if session is None:
            session = DBSession
        manager = BCRYPTPasswordManager()
        hashed = manager.encode(password)
        instance = cls(first=first, last=last, username=username,
                       password=hashed, dflt_medium=dflt_medium,
                       timezone=timezone)
        session.add(instance)
        return instance

    @classmethod
    def check_password(cls, username, password, session=None):
        if session is None:
            session = DBSession
        manager = BCRYPTPasswordManager()
        user = User.by_username(username)
        return manager.check(user.password, password)

    @classmethod
    def get_aliases(cls, username, session=None):
        if session is None:
            session = DBSession
        user = User.by_username(username)
        return user.aliases

    @classmethod
    def by_username(cls, username, session=None):
        if session is None:
            session = DBSession
        return session.query(cls).filter(User.username == username).one()

    def __repr__(self):
        return "<User(first='%s', last='%s', username='%s', \
            dflt_medium='%s')>" % (
            self.first,
            self.last,
            self.username,
            self.dflt_medium)


class Alias(Base):
    """ Alias table; entry created for each User upon instantiation.
        Has a one-to-many relationship with UUID table.
        - alias: alias moniker, which defaults to 'ME';
        - user_id: ForeignKey for the User table;
        - contact_info: either an email address or phone number, whichever is
          provided upon registration
        - medium: 1 for email, 2 for phone
        - activation_state: 0 for unverified, 1 for verified
    """
    __tablename__ = 'aliases'
    id = Column(Integer, primary_key=True, autoincrement=True)
    alias = Column(Unicode(100), default='ME', nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    contact_info = Column(Unicode(75), nullable=False)
    medium = Column(Integer, default=1)
    activation_state = Column(Integer, default=0)

    uuids = relationship(
        'UUID',
        order_by='UUID.id',
        backref=backref('aliases', order_by=id)
    )
    # reminders = relationship(
    #     'Reminder',
    #     order_by='Reminder.id',
    #     backref='aliases'
    # )

    @classmethod
    def create_alias(cls, user_id, contact_info, alias=None,
                     medium=None, activation_state=None, session=None):
        if session is None:
            session = DBSession
        instance = cls(alias=alias, user_id=user_id,
                       contact_info=contact_info, medium=medium,
                       activation_state=activation_state)
        session.add(instance)
        return instance

    @classmethod
    def activate(cls, alias_id, session=None):
        if session is None:
            session = DBSession
        alias = session.query(cls).filter(Alias.id == alias_id).one()
        alias.activation_state = 1

    @classmethod
    def get_user_id(cls, alias_id, session=None):
        if session is None:
            session = DBSession
        alias = Alias.by_id(alias_id)
        return alias.user_id

    @classmethod
    def by_id(cls, alias_id, session=None):
        if session is None:
            session = DBSession
        return session.query(cls).get(alias_id)

    def __repr__(self):
        return "<Alias(name='%s', contact='%s', c_state='%s', \
                user_id='%s')>" % (
            self.alias, self.contact_info,
            self.activation_state, self.user_id)


class UUID(Base):
    """ UUID table; entry created for each Alias upon instantiation.
        - uuid: autogenerated uuid;
        - alias_id: ForeignKey for the Alias table;
        - confirmation_state: provides info on the state of the uuid
          confirmation email.
            0: (default) not sent
            1: email sent (not confirmed)
            2: uuid confirmed
            -1: uuid expired
        - created: autogenerated time stamp
    """
    __tablename__ = 'uuids'
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), nullable=False, default=str(uuid.uuid4()))
    alias_id = Column(Integer, ForeignKey('aliases.id'), nullable=False)
    confirmation_state = Column(Integer, default=0, nullable=False)
    created = Column(
        DateTime,
        default=datetime.utcnow(),
        nullable=False)

    @classmethod
    def create_uuid(cls, alias_id, uuid=None, confirmation_state=None,
                    created=None, session=None):
        if session is None:
            session = DBSession
        instance = cls(alias_id=alias_id, uuid=uuid,
                       confirmation_state=confirmation_state, created=created)
        session.add(instance)
        return instance

    @classmethod
    def email_sent(cls, alias_id, session=None):
        if session is None:
            session = DBSession
        uuid = UUID.by_alias_id(alias_id)
        uuid.confirmation_state = 1

    @classmethod
    def by_alias_id(cls, alias_id, session=None):
        if session is None:
            session = DBSession
        return session.query(cls).filter(UUID.alias_id == alias_id).one()

    @classmethod
    def get_alias(cls, uuid, session=None):
        """Queries for uuid row by uuid; returns a tuple containing
        (uuid.alias_id, uuid.confirmation_state)
        """
        if session is None:
            session = DBSession
        UUID._update_state(uuid)
        uuid = UUID.by_uuid(uuid)
        return (uuid.alias_id, uuid.confirmation_state)

    @classmethod
    def success(cls, uuid, session=None):
        if session is None:
            session = DBSession
        uuid = UUID.by_uuid(uuid)
        uuid.confirmation_state = 2

    @classmethod
    def by_uuid(cls, uuid, session=None):
        if session is None:
            session = DBSession
        uuid = session.query(cls).filter(UUID.uuid == uuid).one()
        return uuid

    @classmethod
    def _update_state(cls, uuid, session=None):
        if session is None:
            session = DBSession
        uuid = UUID.by_uuid(uuid)
        if uuid.confirmation_state != 2:
            eol = uuid.created + timedelta(days=1)
            if eol < datetime.utcnow():
                uuid.confirmation_state = -1

    def __repr__(self):
        return "<UUID(uuid='%s', email_state='%s', created='%s', \
                alias_id='%s')>" % (self.uuid, self.confirmation_state,
                                    self.created, self.alias_id)


# def init_db():
#     engine = create_engine(DATABASE_URL, echo=True)
#     Base.metadata.create_all(engine)


# def helper():
#     biz = User.create_user(username='bizbaz', password='asdf')
#     DBSession.add(biz)
#     DBSession.commit()
#     bizmarkie = Alias.create_alias(biz.id, contact_info='biz@gmail.com')
#     DBSession.add(bizmarkie)
#     DBSession.commit()
#     buuid = UUID.create_uuid(bizmarkie.id)
#     DBSession.add(buuid)
#     DBSession.commit()


# class Jobs(Base):
#     __tablename__ = 'jobs'
#     id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
#     reminder_id = Column(Integer, ForeignKey('reminders.id'))
#     # 0 for awaiting execution, 1 for executed successfully, 2 for failed
#     # excecution, 3 for cancelled
#     job_state = Column(Integer)
#     # execution time in UTC
#     execution_time = Column(DateTime)

