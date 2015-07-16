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
