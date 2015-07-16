# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import pytest
from sqlalchemy import create_engine
from pyramid import testing
from cryptacular.bcrypt import BCRYPTPasswordManager
from sqlalchemy.exc import IntegrityError

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
    # request.addfinalizer(models.Base.metadata.drop_all)
    return connection


@pytest.fixture()
def db_session(request, connection):
    from transaction import abort
    trans = connection.begin()
    request.addfinalizer(trans.rollback)
    request.addfinalizer(abort)

    return models.DBSession


def test_create_user(db_session):
    kwargs = {'first': 'foo', 'last': 'bar', 'username': 'foob',
              'password': 'asdf'}
    kwargs['session'] = db_session
    assert db_session.query(models.User).count() == 0

    user = models.User.create_user(**kwargs)
    assert isinstance(user, models.User)

    assert getattr(user, 'id') is None
    assert getattr(user, 'dflt_medium') == 1
    assert getattr(user, 'timezone') == 'America/Los_Angeles'

    db_session.flush()
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


def test_by_username(db_session):
    expected = models.User.create_user('foo', 'bar')
    db_session.flush()
    actual = models.User.by_username('foo')
    assert expected == actual


def test_by_username_valid_query(db_session):
    with pytest.raises(DataError):
        pass
