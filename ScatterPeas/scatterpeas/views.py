from pyramid.response import Response
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPForbidden
from sqlalchemy.orm.exc import NoResultFound
# import os
# from sqlalchemy.orm import scoped_session, sessoinmaker
# from zope.sqlalchemy import ZopeTransactionExtension
from cryptacular.bcrypt import BCRYPTPasswordManager
from pyramid.security import remember, forget
from pyramid.security import Allow, ALL_PERMISSIONS, Authenticated

from .models import (
    DBSession,
    MyModel,
    )


# this needs to be moved into models once we have them


class User(object):
    @property
    def __acl__(self):
        return [
            (Allow, self.username, 'edit'),
            (Allow, 'group:admin', 'edit')
        ]

    def __init__(self, username, password, first_name=None, last_name=None,
                 email=None, phone=None, default_medium='email',
                 timezone='Pacific', groups=None):
        self.username = username
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.default_medium = default_medium
        self.timezone = timezone
        self.groups = groups or []


class Reminder(object):
    @property
    def __acl__(self):
        return [
            (Allow, self.owner, 'edit'),
            (Allow, 'group:admin', 'edit'),
        ]

    def __init__(self, owner, title, payload, delivery_time):
        self.owner = owner
        self.title = title
        self.payload = payload
        self.delivery_time = delivery_time


USERS = {}
REMINDERS = {}
USERS['user1'] = User('user1', 'password')
USERS['user2'] = User('user2', 'password')
USERS['admin'] = User('admin', 'password', ['admin'])
REMINDERS['myreminder'] = Reminder('user1', 'myreminder', 'take out the garbage', 'a time')
REMINDERS['reminder2'] = Reminder('user2', 'reminder2', 'feed the cat', 'time2')


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
        (Allow, Authenticated, 'create')
    ]

    def __init__(self, request):
        self.request = request

    def __getitem__(self, title):
        return REMINDERS[title]


class UserFactory(object):
    __acl__ = [
        (Allow, 'group:admin', ALL_PERMISSIONS)
    ]

    def __getitem__(self, username):
        return USERS[username]


def groupfinder(userid, request):
    user = USERS.get(userid)
    if user:
        return ['group:%s' % g for g in user.groups]


def do_login(request):
    # username = request.params.get('username', None)
    # password = request.params.get('password', None)
    # if not (username and password):
    #     raise ValueError('both username and password are required')

    # settings = request.registry.settings
    # manager = BCRYPTPasswordManager()
    # if username == settings.get('auth.username', ''):
    #     hashed = settings.get('auth.password', '')
    #     return manager.check(hashed, password)
    # return False
    return True


@view_config(route_name='home', renderer='templates/home.jinja2')
def homepage(request):
    return {}


@view_config(route_name='login', renderer="templates/login.jinja2")
def login(request):
    """authenticate a user by username/password"""
    username = request.params.get('username', '')
    error = ''
    if request.method == 'POST':
        error = "Login Failed"
        authenticated = False
        try:
            authenticated = do_login(request)
        except ValueError as e:
            error = str(e)

        if authenticated:
            headers = remember(request, username)
            return HTTPFound(request.route_url('home'), headers=headers)

    return {'error': error, 'username': username}


@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(request.route_url('home'), headers=headers)


@view_config(route_name='list', renderer='templates/list.jinja2')
def list_reminders(request):
    if not request.authenticated_userid:
        return HTTPFound(request.route_url('login'))
    reminders = []
    for reminder in REMINDERS:
        if REMINDERS[reminder].owner == request.authenticated_userid:
            reminders.append(REMINDERS[reminder])
    return {'reminders': reminders}


@view_config(route_name='detail_reminder', renderer='templates/detail_reminder.jinja2', permission='edit')
def view_one_reminder(request):
    reminder = request.context
    return {'reminder': reminder}


@view_config(route_name='create_reminder', renderer='templates/create_reminder.jinja2', permission='create')
def create_reminder(request):
    if request.method == 'POST':
        owner = request.authenticated_userid
        title = request.params.get('title')
        payload = request.params.get('payload')
        delivery_time = request.params.get('delivery_time')
        REMINDERS[title] = Reminder(owner, title, payload, delivery_time)
        return HTTPFound(request.route_url('list'))
    else:
        return {}


@view_config(route_name='edit_reminder', renderer='templates/edit_reminder.jinja2', permission='edit')
def edit_reminder(request):
    reminder = request.context
    if request.method == 'POST':
        del REMINDERS[reminder.title]
        reminder.owner = request.authenticated_userid
        reminder.title = request.params.get('title')
        reminder.payload = request.params.get('payload')
        reminder.delivery_time = request.params.get('delivery_time')
        REMINDERS[reminder.title] = reminder
        return HTTPFound(request.route_url('list'))
    else:
        return {'reminder': reminder}


@view_config(route_name='create_user', renderer='templates/create_user.jinja2')
def create_user(request):
    if request.method == 'POST':
        username = request.params.get('username')
        password = request.params.get('password')
        first_name = request.params.get('first_name')
        last_name = request.params.get('last_name')
        email = request.params.get('email')
        phone = request.params.get('phone')
        default_medium = request.params.get('default_medium')
        timezone = request.params.get('timezone')
        user = User(username, password, first_name, last_name, email,
                    phone, default_medium, timezone)
        USERS[username] = user
    else:
        return {}


conn_err_msg = """\
Pyramid is having a problem using your SQL database.  The problem
might be caused by one of the following things:

1.  You may need to run the "initialize_ScatterPeas_db" script
    to initialize your database tables.  Check your virtual
    environment's "bin" directory for this script and try to run it.

2.  Your database server may not be running.  Check that the
    database server referred to by the "sqlalchemy.url" setting in
    your "development.ini" file is running.

After you fix the problem, please restart the Pyramid application to
try it again.
"""

