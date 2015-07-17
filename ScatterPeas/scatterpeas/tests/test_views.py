# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytest
import os
import datetime
from sqlalchemy import create_engine
from scatterpeas import models
from webtest import TestApp
from pyramid.paster import get_app
from scatterpeas.models import User, Alias, Reminder, RRule, Job

TEST_DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql:///test_scatterpeas'
)

os.environ['DATABASE_URL'] = TEST_DATABASE_URL

# need some global variables
uuid = ''
alias_id = ''


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
def app(db_session):
    app = get_app('ScatterPeas/testing.ini')
    return TestApp(app)


# fails if the homepage doesn't load
def test_get_home(app):
    response = app.get('/')
    assert response.status_code == 200
    assert 'The pod for all of your scattered peas.' in response.body


# fails if we move the create form out of home; mostly a reminder
# to fix the wiring
def test_get_create_user_form(app):
    response = app.get('/')
    assert response.status_code == 200
    assert 'id="sign-up-form"' in response.body


# this could succeed, fail and return to the homepage with an error
# message for the user, or just blow up in some unforeseen way.
def test_create_user(app):
    global uuid
    global alias_id
    params = {'username': 'user1',
              'password': 'password',
              'first_name': 'bob',
              'last_name': 'hope',
              'contact_info': 'fake@notreal.com',
              }
    response = app.post('/createuser', params=params, status='3*')
    redirected = response.follow()
    assert 'Please wait for your confirmation link' in redirected.body

    # pull the uuid out of the db for the next step
    user = User.by_username('user1')
    alias = user.aliases[0]
    alias_id = alias.id
    uuid = alias.uuids[0].uuid


# can fail if uuid is used or expired, or doesn't exist
def test_confirm_alias(app):
    response = app.get('/confirm/{}'.format(uuid))
    assert response.status_code == 200
    assert 'Success! You may now send reminders to this contact.' in response.body


def test_confirm_bad_uuid(app):
    response = app.get('/confirm/foobar')
    assert response.status_code == 200
    assert 'This is not a valid confirmation link.' in response.body


def login_helper(username, password, app):
    """Encapsulate app login for reuse in tests
    Accept all status codes so that we can make assertions in tests
    """
    login_data = {'username': username, 'password': password}
    return app.post('/login', params=login_data, status='*')


def test_login(app):
    response = login_helper('user1', 'password', app)
    redirected = response.follow()
    assert "Logout" in redirected.body
    response = app.get('/createreminder', status='*')
    assert response.status_code == 200


def test_logout(app):
    login_helper('user1', 'password', app)
    response = app.get('/logout', status='3*')
    redirected = response.follow()
    assert 'Login' in redirected.body
    response = app.get('/createreminder', status='*')
    assert response.status_code == 403


def test_create_reminder(app):
    now = datetime.datetime.now()
    naive_now = now.replace(tzinfo=None)
    job_time = naive_now + datetime.timedelta(minutes=10)
    login_helper('user1', 'password', app)
    params = {'alias_id': alias_id,
              'title': 'test title',
              'payload': 'test body',
              'delivery_time': job_time}
    response = app.post('/createreminder', params=params, status='3*')
    redirected = response.follow()
    assert redirected.status_code == 200
    assert 'test title' in redirected.body


def test_create_reminder_bad_alias(app):
    now = datetime.datetime.now()
    naive_now = now.replace(tzinfo=None)
    job_time = naive_now + datetime.timedelta(minutes=10)
    login_helper('user1', 'password', app)
    params = {'alias_id': 30,
              'title': 'test title',
              'payload': 'test body',
              'delivery_time': job_time}
    response = app.post('/createreminder', params=params, status='*')
    assert response.status_code == 403
    assert "You haven't registered this contact." in response.body