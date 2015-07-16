# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import pytest
from sqlalchemy import create_engine
from pyramid import testing
from sqlalchemy.orm.exc import NoResultFound

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
def my_user(db_session):
    kwargs = {'first': 'foo', 'last': 'bar', 'username': 'foobar',
              'password': 'asdf'}
    kwargs['session'] = db_session
    user = models.User.create_user(**kwargs)
    return user


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


def test_by_username(db_session, my_user):
    expected = my_user
    db_session.flush()
    actual = models.User.by_username('foobar')
    assert expected == actual


def test_by_username_invalid_query(db_session):
    with pytest.raises(NoResultFound):
        models.User.by_username('doesnotexist')


def test_check_password_invalid_user(db_session):
    assert models.User.check_password('doesnotexist', 'asdf') is False


def test_check_password_wrong_password(db_session, my_user):
    user = my_user
    assert models.User.check_password(user.username, 'badpassword') is False


def test_check_password_valid_credentials(db_session, my_user):
    assert models.User.check_password(my_user.username, 'asdf') is True


def test_get_aliases_null(db_session, my_user):
    assert models.User.get_aliases(my_user.username) == []


def test_get_aliases(db_session, my_user):
    my_alias = models.Alias.create_alias(my_user.id, 'foobar@gmail.com')
    assert models.User.get_aliases(my_user.username)[0] == my_alias


def test_get_multiple_aliases(db_session, my_user):
    me = models.Alias.create_alias(my_user.id, 'foobar@gmail.com')
    my_friend = models.Alias.create_alias(my_user.id,
                                          'friend@gmail.com',
                                          alias='friend')
    assert models.User.get_aliases(my_user.username)[0] == me
    assert models.User.get_aliases(my_user.username)[1] == my_friend


def test_get_aliases_invalid_user(db_session):
    with pytest.raises(NoResultFound):
        models.User.get_aliases('badusername')
