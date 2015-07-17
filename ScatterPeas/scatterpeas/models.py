# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from dateutil import parser
from dateutil.rrule import rrule
import sqlalchemy as sa
import os
import uuid
import pytz
from datetime import datetime, timedelta
from pyramid.security import Allow, ALL_PERMISSIONS, Authenticated
import pytz

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
from sqlalchemy.orm.exc import NoResultFound

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
    'postgresql:///scatterpeas2'
)

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))

Base = declarative_base()


# engine = create_engine(DATABASE_URL, echo=True)
# Session = sessionmaker(bind=engine)
# DBSession = Session()


class Reminder(Base):
    """Reminder table includes payload information for reminders, and
    provides functionality for putting jobs onto the jobs table. Columns
    include:
    -id
    -alias_id: ForeignKey to Alias table
    -title: Short version of reminder; required
    -text_payload: To include as email body, optional
    -media_payload: For including pictures etc. Not yet fully implemented.
    -rstate: Tracks whether Reminder has pending jobs. True for active.
    """

    __tablename__ = 'reminders'
    rrule = relationship("RRule", backref="reminders", uselist=False)
    jobs = relationship("Job", backref="reminder")

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    alias_id = Column(Integer, ForeignKey('aliases.id'), nullable=False)
    # keeps the rrule currently generating jobs
    # rrule_id = Column(Integer, ForeignKey('rrules.id'))
    title = Column(Unicode(256), nullable=False)
    text_payload = Column(Unicode(20000))
    # this might end up just being a link to a static resourc; we will see
    media_payload = Column(Unicode(256))
    # rstate is used to to track whether a reminder is still producing jobs
    # turned to False after execution of last job
    rstate = Column(Boolean)

    @property
    def __acl__(self):
        rule_list = []
        for user in self.alias.users:
            rule_list.append((Allow, user.username, 'edit'))
        rule_list.append((Allow, 'group:admin', ALL_PERMISSIONS))

    @classmethod
    def parse_reminder(cls, reminder_id, session=None):
        """Takes a reminder and returns the reminder information needed
        to parse a reminder into a text or email. Also checks for pending jobs,
        instantiates them. Flips rstate to False if current call is the last"""
        if session is None:
            session = DBSession
        next_job = cls.get_next_job(reminder_id)
        reminder = cls.retrieve_instance(reminder_id)
        if next_job is None:
            reminder.rstate = False
        else:
            Job.create_job(reminder_id, next_job)
        return {"title": reminder.title,
                "text_payload": reminder.text_payload,
                "media_payload": reminder.media_payload,
                "alias_id": reminder.alias_id}

    @classmethod
    def retrieve_instance(cls, reminder_id, session=None):
        """Retrieves a reminder instance from reminder_id"""
        if session is None:
            session = DBSession
        return session.query(Reminder).filter(Reminder.id == reminder_id).one()

    @classmethod
    def get_next_job(cls, reminder_id, session=None):
        """Takes a reminder_id to retrieve current rrule set and generate
        the next job in datetime format for utc. Returns None if there is
        no next job."""
        if session is None:
            session = DBSession
        reminder = cls.retrieve_instance(reminder_id)
        dtstart = RRule.get_rrules(reminder.rrule.id)
        rrule_gen = rrule(0, dtstart=dtstart, count=1)
        now = datetime.utcnow()
        next_job = rrule_gen.after(now)
        if next_job is None:
            return None
        else:
            return next_job

    @classmethod
    def create_reminder(cls, alias_id=0, title="",
                        text_payload="", media_payload="",
                        rstate=True, session=None):
        '''Instantiates a Reminder instance. An RRule object is required
        for the Reminder. We currently require any parent function to
        attach an rrule_id to the Reminder after instantiation; the
        Reminder object is not valid without this
        '''
        if session is None:
            session = DBSession
        if title != "" and alias_id != 0:
            instance = cls(title=title, alias_id=alias_id,
                           text_payload=text_payload,
                           media_payload=media_payload, rstate=rstate)
            session.add(instance)
            session.flush()
            return instance


class RRule(Base):
    """Contains iCal specification rules corresponding to an event. This
    class is not yet fully implemented, but stands in for future
    expandability"""
    __tablename__ = 'rrules'

    # constrain this to primary key of reminders
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    reminder_id = Column(Integer, ForeignKey('reminders.id'))
    dtstart = Column(DateTime)

    @classmethod
    def get_rrules(cls, rrule_id, session=None):
        if session is None:
            session = DBSession
        # Passes back just dtstart for now; future implementations should
        # probably use a dictionary
        return session.query(RRule).filter(RRule.id == rrule_id).one().dtstart

    @classmethod
    def create_rrule(cls, reminder_id=0,
                     dtstart=(datetime.utcnow() + timedelta(hours=24)),
                     session=None):
        if session is None:
            session = DBSession
        try:
            # This try block can disappear when we refactor to use the ORM
            # more idiomatically
            Reminder.retrieve_instance(reminder_id)
        except NoResultFound:
            raise NoResultFound
        else:
            instance = cls(reminder_id=reminder_id, dtstart=dtstart)
            session.add(instance)
            session.flush()
            return instance

    @property
    def display_time(self):
        dt = self.dtstart.replace(tzinfo=None)
        utc_dt = pytz.utc.localize(dt)
        local_dt = utc_dt.astimezone(pytz.timezone("US/Pacific"))
        return local_dt.strftime('%Y/%m/%d %R')
        return "see if this works"


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    first = Column(Unicode(50))
    last = Column(Unicode(50))
    username = Column(Unicode(50), nullable=False, unique=True)
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

    @property
    def __acl__(self):
        return [
            (Allow, self.username, 'edit'),
            (Allow, 'group:admin', 'edit')
        ]

    @classmethod
    def create_user(cls, username, password, first="", last="",
                    dflt_medium=1, timezone='America/Los_Angeles',
                    session=None):
        """Instantiates a new user, and writes it to the database.
        User must supply a username and password.
        """
        if session is None:
            session = DBSession
        manager = BCRYPTPasswordManager()
        hashed = manager.encode(password)
        instance = cls(first=first, last=last, username=username,
                       password=hashed, dflt_medium=dflt_medium,
                       timezone=timezone)
        session.add(instance)
        session.flush()
        return instance

    @classmethod
    def check_password(cls, username, password, session=None):
        if session is None:
            session = DBSession
        manager = BCRYPTPasswordManager()
        try:
            user = User.by_username(username)
        except NoResultFound:
            return False
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

    def __eq__(self, other):
        return isinstance(other, User) and other.id == self.id


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
    reminders = relationship("Reminder", backref="alias")
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

    @property
    def __acl__(self):
        rule_list = []
        for user in self.users:
            rule_list.append((Allow, user.username, 'edit'))
        rule_list.append((Allow, 'group:admin', ALL_PERMISSIONS))
        return rule_list

    @classmethod
    def create_alias(cls, user_id, contact_info, alias=None,
                     medium=None, activation_state=None, session=None):
        if session is None:
            session = DBSession
        instance = cls(alias=alias, user_id=user_id,
                       contact_info=contact_info, medium=medium,
                       activation_state=activation_state)
        session.add(instance)
        session.flush()
        return instance

    @classmethod
    def retrieve_instance(cls, alias_id, session=None):
        """Retrieve an alias instance from alias_id"""
        if session is None:
            session = DBSession
        return session.query(Alias).filter(Alias.id == alias_id).one()

    @classmethod
    def activate(cls, alias_id, session=None):
        if session is None:
            session = DBSession
        alias = Alias.by_id(alias_id)
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

    def __eq__(self, other):
        return other.id == self.id

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
        uuid = uuid.uuid4()
        instance = cls(alias_id=alias_id, uuid=uuid,
                       confirmation_state=confirmation_state, created=created)
        session.add(instance)
        session.flush()
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
        """Query for uuid row by uuid; return a tuple containing
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
        if uuid.confirmation_state != -1 and uuid.confirmation_state != 0:
            uuid.confirmation_state = 2

    @classmethod
    def by_uuid(cls, uuid, session=None):
        if session is None:
            session = DBSession
        return session.query(cls).filter(UUID.uuid == uuid).one()

    @classmethod
    def _update_state(cls, uuid, session=None):
        if session is None:
            session = DBSession
        uuid = UUID.by_uuid(uuid)
        if uuid.confirmation_state != 2:
            eol = uuid.created + timedelta(days=1)
            if eol < datetime.utcnow():
                uuid.confirmation_state = -1

    def __eq__(self, other):
        return isinstance(other, UUID) and other.id == self.id

    def __repr__(self):
        return "<UUID(uuid='%s', email_state='%s', created='%s', \
                alias_id='%s')>" % (self.uuid, self.confirmation_state,
                                    self.created, self.alias_id)


class Job(Base):
    """Job table contains jobs that will be sent out"""
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    reminder_id = Column(Integer, ForeignKey('reminders.id'))
    # 0 for awaiting execution, 1 for executed successfully, 2 for failed
    # excecution, 3 for cancelled
    job_state = Column(Integer)
    # execution time in UTC
    execution_time = Column(DateTime)

    def mark_complete(self):
        """Mark a job as completed. Call on an instance of a job after the job
        has been completed by a parent task."""

        if self.job_state in set([0, 2]):
            self.job_state = 1
            return True
        else:
            #  Case of job not being in an appropriate state to execute
            return False

    @classmethod
    def create_job(cls, reminder_id, execution_time, session=None):
        if session is None:
            session = DBSession
        try:
            # This try block can disappear when we refactor to use the ORM
            # more idiomatically
            Reminder.retrieve_instance(reminder_id)
        except NoResultFound:
            raise NoResultFound
        else:
            instance = cls(reminder_id=reminder_id,
                           execution_time=execution_time, job_state=0)
            session.add(instance)
        return instance

    @classmethod
    def retrieve_instance(cls, job_id, session=None):
        if session is None:
            session = DBSession
        return session.query(Job).filter(Job.id == job_id).one()

    @classmethod
    def todo(cls, minutes_out=0, session=None):
        """Return a list of job objects that should be excecuted from now to
        an optional number of minute(s) out"""
        if session is None:
            session = DBSession
        now = datetime.utcnow()
        query_time = now + timedelta(minutes=minutes_out)
        return session.query(cls).filter(
            Job.execution_time < query_time).all()


class RootFactory(object):
    __acl__ = [
        (Allow, 'group:admin', ALL_PERMISSIONS),
        (Allow, Authenticated, 'create')
    ]

    def __init__(self, request):
        self.request = request


class ReminderFactory(object):
    __acl__ = [
        (Allow, 'group:admin', ALL_PERMISSIONS),
    ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, id):
        return Reminder.retrieve_instance(id)


class UserFactory(object):
    __acl__ = [
        (Allow, 'group:admin', ALL_PERMISSIONS)
    ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, username):
        return User.by_username(username)


class AliasFactory(object):
    __acl__ = [
        (Allow, 'group:admin', ALL_PERMISSIONS)
    ]

    def __init__(self, request):
        self.request = request

    def __getitem(self, id):
        return Alias.by_id(id)


def groupfinder(username, request):
    try:
        user = User.by_username(username)
    except NoResultFound:
        return None
    return ['group:%s' % g for g in user.groups]


def init_db():
    engine = sa.create_engine(DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)


def helper():
    user1 = User.create_user('jaytyler', 'secretpass', 'jason', 'tyler')
    user2 = User.create_user('ryty', 'othersecret', 'ryan', 'tyler')
    user3 = User.create_user('nick', 'nickpassword', 'nick', 'draper')
    user4 = User.create_user('saki', 'nakedmolerats', 'saki', 'fu')
    user5 = User.create_user('grace', 'gatitapass', 'grace', 'hata')
    DBSession.commit()
    alias1 = Alias.create_alias(1, "jmtyler@gmail.com", "ME", 1)
    alias2 = Alias.create_alias(1, "206-679-9510", "ME", 2)
    alias3 = Alias.create_alias(2, "theryty@gmail.com", 1)
    alias4 = Alias.create_alias(3, "nickemail@email.com", 1)
    alias5 = Alias.create_alias(4, "sakiemail@email.com", 1)
    alias6 = Alias.create_alias(5, "graceemail@email.com", 1)
    DBSession.commit()
    reminder1 = Reminder.create_reminder(1, "Here's an email to send to \
                                         Jason's email")
    reminder2 = Reminder.create_reminder(2, "Heres a text to send to \
                                         Jason's phone")
    reminder3 = Reminder.create_reminder(3, "Here's a email to send to Ryan")
    reminder4 = Reminder.create_reminder(4, "Here's an email to send to Nick")
    reminder5 = Reminder.create_reminder(5, "Here's an email to send to Saki")
    reminder6 = Reminder.create_reminder(6, "Here's an email to send to Grace")
    DBSession.commit()
    rrule1 = RRule.create_rrule(1, datetime(2015, 7, 16, 18))
    rrule2 = RRule.create_rrule(2, datetime(2015, 7, 16, 19))
    rrule3 = RRule.create_rrule(3, datetime(2015, 7, 16, 20))
    rrule4 = RRule.create_rrule(4, datetime(2015, 7, 16, 21))
    rrule5 = RRule.create_rrule(5, datetime(2015, 7, 16, 22))
    rrule6 = RRule.create_rrule(6, datetime(2015, 7, 16, 23))
    DBSession.commit()
    users = [user1, user2, user3, user4, user5]
    aliases = [alias1, alias2, alias3, alias4, alias5, alias6]
    reminders = [reminder1, reminder2, reminder3, reminder4, reminder5,
                 reminder6]
    return (users, aliases, reminders)


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
