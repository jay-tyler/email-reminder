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
DBSession1 = Session()

class Reminders(Base):

    __tablename__ = 'reminders'

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
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


class RRules(Base):
    """Contains iCal specification rules corresponding to an event. """
    __tablename__ = 'rrules'
    # constrain this to primary key of reminders
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    reminder_id = Column(Integer, ForeignKey('reminders.id'))


class Jobs(Base):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    reminder_id = Column(Integer, ForeignKey('reminders.id'))
    # 0 for awaiting execution, 1 for executed successfully, 2 for failed
    # excecution, 3 for cancelled
    job_state = Column(Integer)
    # execution time in UTC
    execution_time = Column(DateTime)