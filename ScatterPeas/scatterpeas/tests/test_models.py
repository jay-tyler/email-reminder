# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import pytest
from sqlalchemy import create_engine
from pyramid import testing
from sqlalchemy.orm.exc import NoResultFound
import uuid as pyuuid
from datetime import timedelta

from scatterpeas import models
from scatterpeas.models import User, Alias, Reminder, RRule, Job
from datetime import datetime, timedelta


TEST_DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql:///test_scatterpeas'
)

os.environ['DATABASE_URL'] = TEST_DATABASE_URL


@pytest.fixture(scope='session')
def connection(request):
    engine = create_engine(TEST_DATABASE_URL)
    models.Base.metadata.create_all(engine)
    connection = engine.connect()
    models.DBSession.registry.clear()
    models.DBSession.configure(bind=connection)
    models.Base.metadata.bind = engine
    request.addfinalizer(models.Base.metadata.drop_all)
    return connection


@pytest.fixture()
def db_session(request, connection):
    from transaction import abort
    trans = connection.begin()
    request.addfinalizer(trans.rollback)
    request.addfinalizer(abort)

    return models.DBSession


@pytest.fixture()
def user(db_session):
    kwargs = {'first': 'foo', 'last': 'bar', 'username': 'foobar',
              'password': 'asdf'}
    kwargs['session'] = db_session
    user = models.User.create_user(**kwargs)
    return user


@pytest.fixture()
def alias(db_session, user):
    kwargs = {'user_id': user.id, 'contact_info': 'myalias@gmail.com'}
    kwargs['session'] = db_session
    alias = models.Alias.create_alias(**kwargs)
    return alias


@pytest.fixture()
def active_alias(db_session, user):
    kwargs = {'user_id': user.id,
              'contact_info': 'myalias@gmail.com',
              'activation_state': 1}
    kwargs['session'] = db_session
    alias = models.Alias.create_alias(**kwargs)
    return alias


@pytest.fixture()
def uuid(db_session, alias):
    kwargs = {'alias_id': alias.id, 'session': db_session}
    uuid = models.UUID.create_uuid(**kwargs)
    return uuid


@pytest.fixture()
def setup_session(db_session):
    """Instantiate a session for testing objects"""
    user1 = User.create_user(
        'jaytyler', 'secretpass', 'jason', 'tyler', session=db_session)
    user2 = User.create_user(
        'ryty', 'othersecret', 'ryan', 'tyler', session=db_session)
    user3 = User.create_user(
        'nick', 'nickpassword', 'nick', 'draper', session=db_session)
    user4 = User.create_user(
        'saki', 'nakedmolerats', 'saki', 'fu', session=db_session)
    user5 = User.create_user(
        'grace', 'gatitapass', 'grace', 'hata', session=db_session)
    db_session.flush()
    alias1 = Alias.create_alias(
        user1.id, "jmtyler@gmail.com", "ME", 1, session=db_session)
    alias2 = Alias.create_alias(
        user1.id, "206-659-4510", "ME", 2, session=db_session)
    alias3 = Alias.create_alias(
        user2.id, "ryanty@gmail.com", "ME", 1, session=db_session)
    alias4 = Alias.create_alias(
        user3.id, "nickemail@email.com", "ME", 1, session=db_session)
    alias5 = Alias.create_alias(
        user4.id, "sakiemail@email.com", "ME", 1, session=db_session)
    alias6 = Alias.create_alias(
        user5.id, "graceemail@email.com", "ME", 1, session=db_session)
    db_session.flush()
    reminder1 = Reminder.create_reminder(
        alias1.id, "Here's an email to send to Jason's email",
        session=db_session)
    reminder2 = Reminder.create_reminder(alias2.id,
        "Heres a text to send to Jason's phone", session=db_session)
    reminder3 = Reminder.create_reminder(alias3.id,
        "Here's a email to send to Ryan", session=db_session)
    reminder4 = Reminder.create_reminder(alias4.id,
        "Here's an email to send to Nick", session=db_session)
    reminder5 = Reminder.create_reminder(alias5.id,
        "Here's an email to send to Saki", session=db_session)
    reminder6 = Reminder.create_reminder(alias6.id,
        "Here's an email to send to Grace", session=db_session)
    db_session.flush()
    now = datetime.utcnow()
    rrule1 = RRule.create_rrule(reminder1.id, now + timedelta(hours=-3),
                                session=db_session)
    rrule2 = RRule.create_rrule(reminder2.id, now + timedelta(hours=-2),
                                session=db_session)
    rrule3 = RRule.create_rrule(reminder3.id, now + timedelta(hours=-1),
                                session=db_session)
    rrule4 = RRule.create_rrule(reminder4.id, now + timedelta(hours=1),
                                session=db_session)
    rrule5 = RRule.create_rrule(reminder5.id, now + timedelta(hours=2),
                                session=db_session)
    rrule6 = RRule.create_rrule(reminder6.id, now + timedelta(hours=3),
                                session=db_session)
    db_session.flush()
    users = [user1, user2, user3, user4, user5]
    aliases = [alias1, alias2, alias3, alias4, alias5, alias6]
    reminders = [reminder1, reminder2, reminder3, reminder4, reminder5,
                 reminder6]
    return (users, aliases, reminders)


def test_create_user(db_session):
    kwargs = {'first': 'foo', 'last': 'bar', 'username': 'foobar',
              'password': 'asdf'}
    kwargs['session'] = db_session
    assert db_session.query(models.User).count() == 0

    user = models.User.create_user(**kwargs)
    assert isinstance(user, models.User)

    assert getattr(user, 'id') is not None
    assert getattr(user, 'dflt_medium') == 1
    assert getattr(user, 'timezone') == 'America/Los_Angeles'

    assert db_session.query(models.User).count() == 1
    for field in kwargs:
        if field != 'session' and field != 'password':
            assert getattr(user, field) == kwargs[field]

    assert getattr(user, 'id') is not None


def test_username_not_null(db_session):
    bad_data = {'first': 'foo', 'last': 'bar', 'password': 'asdf'}
    with pytest.raises(TypeError):
        models.User.create_user(session=db_session, **bad_data)


def test_password_not_null(db_session):
    bad_data = {'first': 'foo', 'last': 'bar', 'username': 'foo'}
    with pytest.raises(TypeError):
        models.User.create_user(session=db_session, **bad_data)


def test_first_and_last_not_required(db_session):
    kwargs = {'username': 'foo', 'password': 'asdf'}
    kwargs['session'] = db_session
    user = models.User.create_user(**kwargs)
    assert isinstance(user, models.User)


def test_by_username(db_session, user):
    expected = user
    db_session.flush()
    actual = models.User.by_username('foobar')
    assert expected == actual


def test_by_username_invalid_query(db_session):
    with pytest.raises(NoResultFound):
        models.User.by_username('doesnotexist')


def test_check_password_invalid_user(db_session):
    assert models.User.check_password('doesnotexist', 'asdf') is False


def test_check_password_wrong_password(db_session, user):
    assert models.User.check_password(user.username, 'badpassword') is False


def test_check_password_valid_credentials(db_session, user):
    assert models.User.check_password(user.username, 'asdf') is True


def test_get_aliases_null(db_session, user):
    assert models.User.get_aliases(user.username) == []


def test_get_aliases(db_session, user):
    my_alias = models.Alias.create_alias(user.id, 'foobar@gmail.com')
    assert models.User.get_aliases(user.username)[0] == my_alias


def test_get_multiple_aliases(db_session, user):
    me = models.Alias.create_alias(user.id, 'foobar@gmail.com')
    my_friend = models.Alias.create_alias(user.id,
                                          'friend@gmail.com',
                                          alias='friend')
    assert models.User.get_aliases(user.username)[0] == me
    assert models.User.get_aliases(user.username)[1] == my_friend


def test_get_aliases_invalid_user(db_session):
    with pytest.raises(NoResultFound):
        models.User.get_aliases('badusername')


def test_create_alias(db_session, user):
    kwargs = {'user_id': user.id, 'contact_info': 'myalias@gmail.com'}
    kwargs['session'] = db_session
    assert db_session.query(models.Alias).count() == 0

    alias = models.Alias.create_alias(**kwargs)
    assert isinstance(alias, models.Alias)

    assert getattr(alias, 'id') is not None
    assert getattr(alias, 'alias') == 'ME'
    assert getattr(alias, 'medium') == 1
    assert getattr(alias, 'activation_state') == 0

    assert db_session.query(models.Alias).count() == 1
    for field in kwargs:
        if field != 'session':
            assert getattr(alias, field) == kwargs[field]


def test_create_alias_contact_info_not_null(db_session, user):
    bad_data = {'user_id': user.id, 'session': db_session}
    with pytest.raises(TypeError):
        models.Alias.create_alias(**bad_data)


def test_retrieve_instance(db_session, alias):
    expected = alias
    db_session.flush()
    actual = models.Alias.retrieve_instance(alias.id)
    assert expected == actual


def test_retrieve_instance_invalid_query(db_session):
    with pytest.raises(NoResultFound):
        models.Alias.retrieve_instance(5)


def test_activate(db_session, alias):
    assert alias.activation_state == 0
    models.Alias.activate(alias.id)
    assert alias.activation_state == 1


def test_activate_active_alias(db_session, active_alias):
    assert active_alias.activation_state == 1
    models.Alias.activate(active_alias.id)
    assert active_alias.activation_state == 1


def test_activate_invalid_alias(db_session):
    assert db_session.query(models.Alias).count() == 0
    with pytest.raises(AttributeError):
        models.Alias.activate(5)


def test_get_user_id(db_session, user, alias):
    assert models.Alias.get_user_id(alias.id) == user.id


def test_get_user_id_invalid_alias(db_session):
    assert db_session.query(models.Alias).count() == 0
    with pytest.raises(AttributeError):
        models.Alias.get_user_id(5)


def test_by_id(db_session, alias):
    expected = alias
    db_session.flush()
    actual = models.Alias.by_id(alias.id)
    assert expected == actual


def test_by_id_invalid_query(db_session):
    assert db_session.query(models.Alias).count() == 0
    assert models.Alias.by_id(5) is None


def test_create_uuid(db_session, alias):
    kwargs = {'alias_id': alias.id, 'session': db_session}
    assert db_session.query(models.UUID).count() == 0

    uuid = models.UUID.create_uuid(**kwargs)
    assert isinstance(uuid, models.UUID)

    for auto in ['id', 'uuid', 'created']:
        assert getattr(uuid, auto, None) is not None

    assert getattr(uuid, 'confirmation_state') == 0
    assert getattr(uuid, 'alias_id') == alias.id

    assert db_session.query(models.Alias).count() == 1


def test_alias_id_not_null(db_session):
    with pytest.raises(TypeError):
        models.UUID.create_uuid()


def test_email_sent(db_session, uuid):
    assert uuid.confirmation_state == 0
    models.UUID.email_sent(uuid.alias_id)
    assert uuid.confirmation_state == 1


def test_email_sent_invalid_uuid(db_session):
    assert db_session.query(models.UUID).count() == 0
    with pytest.raises(NoResultFound):
        models.UUID.email_sent(5)


def test_by_alias_id(db_session, alias, uuid):
    expected = uuid
    actual = models.UUID.by_alias_id(alias.id)
    assert expected == actual


def test_by_alias_id_invalid_query(db_session):
    assert db_session.query(models.UUID).count() == 0
    with pytest.raises(NoResultFound):
        models.UUID.by_alias_id(5)


def test_by_uuid(db_session, uuid):
    expected = uuid
    actual = models.UUID.by_uuid(uuid.uuid)
    assert expected == actual


def test_by_uuid_invalid_query(db_session):
    assert db_session.query(models.UUID).count() == 0
    with pytest.raises(NoResultFound):
        models.UUID.by_uuid(str(pyuuid.uuid4()))


def test_by_uuid_no_query(db_session):
    with pytest.raises(TypeError):
        models.UUID.by_uuid()


def test_get_alias(db_session, uuid):
    expected = (uuid.alias_id, uuid.confirmation_state)
    actual = models.UUID.get_alias(uuid.uuid)
    assert expected == actual


def test_get_alias_invalid_query(db_session):
    assert db_session.query(models.UUID).count() == 0
    with pytest.raises(NoResultFound):
        models.UUID.get_alias(str(pyuuid.uuid4()))


def test_success(db_session, uuid):
    uuid.confirmation_state = 1
    models.UUID.success(uuid.uuid)
    assert uuid.confirmation_state == 2


def test_success_email_not_sent(db_session, uuid):
    models.UUID.success(uuid.uuid)
    assert uuid.confirmation_state == 0


def test_success_expired_uuid(db_session, uuid):
    uuid.confirmation_state = -1
    models.UUID.success(uuid.uuid)
    assert uuid.confirmation_state == -1


def test_update_state_unexpired_uuid(db_session, uuid):
    models.UUID._update_state(uuid.uuid)
    assert uuid.confirmation_state == 0


def test_update_state_expired_uuid(db_session, uuid):
    uuid.created -= timedelta(days=2)
    models.UUID._update_state(uuid.uuid)
    assert uuid.confirmation_state == -1


def test_update_state_already_confirmted(db_session, uuid):
    uuid.confirmation_state = 2
    models.UUID._update_state(uuid.uuid)
    assert uuid.confirmation_state == 2


def test_update_state_invalid_uuid(db_session):
    assert db_session.query(models.UUID).count() == 0
    with pytest.raises(NoResultFound):
        models.UUID._update_state(str(pyuuid.uuid4()))


def test_reminder_create_reminder_valid(db_session, setup_session):
    users, aliases, reminders = setup_session
    past_reminders = db_session.query(Reminder).all()
    out = Reminder.create_reminder(alias_id=aliases[3].id,
                                   title="Here's a title",
                                   session=db_session)
    present_reminders = db_session.query(Reminder).all()
    assert out is not None
    assert len(past_reminders) + 1 == len(present_reminders)


def test_reminder_create_reminder_no_title(db_session, setup_session):
    users, aliases, reminders = setup_session
    past_reminders = db_session.query(Reminder).all()
    out = Reminder.create_reminder(alias_id=aliases[3].id,
                                   session=db_session)
    present_reminders = db_session.query(Reminder).all()
    assert out is None
    assert len(past_reminders) == len(present_reminders)


def test_reminder_create_reminder_no_alias(db_session, setup_session):
    users, aliases, reminders = setup_session
    past_reminders = db_session.query(Reminder).all()
    out = Reminder.create_reminder(title="Here's a title",
                                   session=db_session)
    present_reminders = db_session.query(Reminder).all()
    assert out is None
    assert len(past_reminders) == len(present_reminders)


def test_reminder_retrieve_instance_valid(db_session, setup_session):
    users, aliases, reminders = setup_session
    out = Reminder.retrieve_instance(reminders[4].id, session=db_session)
    assert isinstance(out, Reminder)


def test_reminder_retrieve_instance_invalid(db_session, setup_session):
    users, aliases, reminders = setup_session
    with pytest.raises(NoResultFound):
        out = Reminder.retrieve_instance(1200)


def test_reminder_get_next_job_exists(db_session, setup_session):
    users, aliases, reminders = setup_session
    future_reminder = reminders[3]
    out = Reminder.get_next_job(future_reminder.id, session=db_session)
    assert isinstance(out, datetime)
    assert datetime.utcnow() < out


def test_reminder_get_next_job_absent(db_session, setup_session):
    users, aliases, reminders = setup_session
    future_reminder = reminders[1]
    out = Reminder.get_next_job(future_reminder.id, session=db_session)
    assert out is None


def test_reminder_parse_reminder_upcoming_job(db_session, setup_session):
    users, aliases, reminders = setup_session
    past_jobs = db_session.query(Job).all()
    future_reminder = reminders[3]
    out = Reminder.parse_reminder(future_reminder.id, session=db_session)
    future_jobs = db_session.query(Job).all()
    assert future_reminder.rstate is True
    assert len(past_jobs) + 1 == len(future_jobs)
    assert out is not None


def test_reminder_parse_reminder_jobs_in_past(db_session, setup_session):
    users, aliases, reminders = setup_session
    past_jobs = db_session.query(Job).all()
    past_reminder = reminders[1]
    out = Reminder.parse_reminder(past_reminder.id, session=db_session)
    future_jobs = db_session.query(Job).all()
    assert past_reminder.rstate is False
    assert len(past_jobs) == len(future_jobs)
    assert out is not None


def test_rrule_get_rrules_valid(db_session, setup_session):
    users, aliases, reminders = setup_session
    reminder = reminders[0]
    out = RRule.get_rrules(reminder.id, session=db_session)
    assert isinstance(out, datetime)


def test_rrule_get_rrules_invalid(db_session, setup_session):
    users, aliases, reminders = setup_session
    with pytest.raises(NoResultFound):
        out = RRule.get_rrules(1200, session=db_session)


def test_rrule_create_valid(db_session, setup_session):
    users, aliases, reminders = setup_session
    new_reminder = Reminder.create_reminder(alias_id=aliases[3].id,
                                            title="Here's a title",
                                            session=db_session)
    now = datetime.utcnow()
    RRule.create_rrule(new_reminder.id, now, session=db_session)


def test_rrule_create_invalid(db_session, setup_session):
    users, aliases, reminders = setup_session
    now = datetime.utcnow()
    with pytest.raises(NoResultFound):
        RRule.create_rrule(1200, now)


def test_job_create_valid(db_session, setup_session):
    users, aliases, reminders = setup_session
    future_reminder = reminders[3]
    past_jobs = db_session.query(Job).all()
    job_time = Reminder.get_next_job(future_reminder.id,
                                     session=db_session)
    new_job = Job.create_job(future_reminder.id, job_time, session=db_session)
    present_jobs = db_session.query(Job).all()
    assert len(past_jobs) + 1 == len(present_jobs)
    assert isinstance(new_job, Job)


def test_job_create_invalid(db_session, setup_session):
    users, aliases, reminders = setup_session
    job_time = datetime.utcnow()
    with pytest.raises(NoResultFound):
        Job.create_job(1200, job_time, session=db_session)


def test_job_mark_complete_valid(db_session, setup_session):
    users, aliases, reminders = setup_session
    future_reminder = reminders[3]
    job_time = Reminder.get_next_job(future_reminder.id,
                                     session=db_session)
    new_job = Job.create_job(future_reminder.id, job_time,
                             session=db_session)
    assert new_job.job_state == 0
    out = new_job.mark_complete()
    assert new_job.job_state == 1
    assert out is True


def test_job_mark_complete_valid(db_session, setup_session):
    users, aliases, reminders = setup_session
    future_reminder = reminders[3]
    job_time = Reminder.get_next_job(future_reminder.id,
                                     session=db_session)
    new_job = Job.create_job(future_reminder.id, job_time,
                             session=db_session)
    new_job.mark_complete()
    # Try to flip rstate again
    out = new_job.mark_complete()
    assert out is False
    assert new_job.job_state == 1


def test_job_todo_over_hour_out(db_session, setup_session):
    users, aliases, reminders = setup_session

    for reminder in reminders:
        out = Reminder.parse_reminder(reminder.id, session=db_session)
    todo_list = Job.todo(90, session=db_session)
    assert len(todo_list) == 1
    for job in todo_list:
        assert job.execution_time > datetime.utcnow()


def test_job_todo_over_two_hours_out(db_session, setup_session):
    users, aliases, reminders = setup_session

    for reminder in reminders:
        out = Reminder.parse_reminder(reminder.id, session=db_session)
    todo_list = Job.todo(160, session=db_session)
    assert len(todo_list) == 2
    for job in todo_list:
        assert job.execution_time > datetime.utcnow()
