# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytest
import os
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
    uuid = alias.uuids[0].uuid


def test_confirm_alias(app):
    response = app.get('/confirm/{}'.format(uuid))
    assert response.status_code == 200
    assert 'Success! You may now send reminders to this contact.' in response.body
