from sqlalchemy import create_engine
from sqlalchemy import Integer, ForeignKey, String, Column
from sqlalchemy.types import DateTime, Unicode, Boolean
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://jason@localhost:5432/modeltest')
engine = create_engine(DATABASE_URL, echo=True)


Base = declarative_base()

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
DBSession = Session()


class Reminders(Base):

    __tablename__ = 'reminders'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    alias_id = Column(Integer, ForeignKey('aliases.id'), nullable=False)
    # keeps the rrule currently generating jobs
    rrule_id = Column(Integer, ForeignKey('rrules.id'), nullable=False)
    title = Column(Unicode(256), nullable=False)
    text_payload = Column(Unicode(20000))
    # this might end up just being a link to a static resourc; we will see
    media_payload = Column(Unicode(256))
    # rstate is used to to track whether a reminder is still producing jobs
    # turned to False after execution of last job
    rstate = Column(Integer)
    # next_event = Column(DateTime(timezone=True))
    child = relationship("", backref=backref("reminders", uselist=False))

    @classmethod
    def create(cls, title="", text_payload="", media_payload="",
               rstate=True, session=None, user_id=0, alias_id=0):
        if session is None:
            session = DBSession
        if title != "" and alias_id != 0:
            '''Reminder instance is created, but may not potentially have
            all necessary attributes including rrule_id. It is the parent 
            function's responsibility to provide
            these.
            '''
            instance = cls(title=title,
                           text_payload=text_payload,
                           media_payload=media_payload, rstate=rstate)
            session.add(instance)
            return instance


class RRules(Base):
    """Contains iCal specification rules corresponding to an event. This
    class is not yet fully implemented, but stands in for future
    expandability"""
    __tablename__ = 'rrules'
    # constrain this to primary key of reminders
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    reminder_id = Column(Integer, ForeignKey('reminders.id'))

    @classmethod
    def create(cls, reminder_id=0, session=None):
        if session is None:
            session = DBSession
        if reminder_id != 0:
            instance = cls(reminder_id=reminder_id)
            session.add(instance)
            return instance


class Jobs(Base):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    reminder_id = Column(Integer, ForeignKey('reminders.id'))
    # 0 for awaiting execution, 1 for executed successfully, 2 for failed
    # excecution, 3 for cancelled
    job_state = Column(Integer)
    # execution time in UTC
    execution_time = Column(DateTime)