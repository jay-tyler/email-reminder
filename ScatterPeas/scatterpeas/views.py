from pyramid.response import Response
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPForbidden
# import os
# from sqlalchemy.orm import scoped_session, sessoinmaker
# from zope.sqlalchemy import ZopeTransactionExtension
from cryptacular.bcrypt import BCRYPTPasswordManager
from pyramid.security import remember, forget

from .models import (
    DBSession,
    MyModel,
    )


def do_login(request):
    username = request.params.get('username', None)
    password = request.params.get('password', None)
    if not (username and password):
        raise ValueError('both username and password are required')

    settings = request.registry.settings
    manager = BCRYPTPasswordManager()
    if username == settings.get('auth.username', ''):
        hashed = settings.get('auth.password', '')
        return manager.check(hashed, password)
    return False


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


@view_config(route_name='list', renderer='list.jinja2', factory=ReminderFactory)
def list_reminders(request):
    if request.authenticated_userid:
        reminders = Reminder.search(request.authenticated_userid).all()
        return {'reminders': reminders}
    else:
        return HTTPFound(request.route_url('login'))


@view_config(route_name='detail_reminder', renderer='detail_reminder.jinja2')
def view_one_reminder(request):
    if not request.authenticated_userid:
        return HTTPFound(request.route_url('login'))
    reminder_id = request.matchdict.get('id', None)
    try:
        reminder = Reminder.search(reminder_id).one()
    except NoResultFound:
        return HTTPNotFound('There is no reminder with this id.')
    if request.authenticated_userid == reminder.owner:
        return {'reminder': reminder}
    else:
        return HTTPForbidden()


@view_config(route_name='create_reminder', renderer='create_reminder.jinja2')
def create_reminder(request):
    if not request.authenticated_userid:
        return HTTPFound(request.route_url('login'))
    if request.method == 'POST':
        owner = request.authenticated_userid
        title = request.params.get('title')
        payload = request.params.get('payload')
        delivery_time = request.params.get('delivery_time')
        Reminder.write(owner=owner,
                       title=title,
                       payload=payload,
                       delivery_time=delivery_time)
        return HTTPFound(request.route_url('list'))
    else:
        return {}


@view_config(route_name='edit_reminder', renderer='edit_reminder.jinja2')
def edit_reminder(request):
    if not request.authenticated_userid:
        return HTTPFound(request.route_url('login'))
    reminder = Reminder.search(reminder_id).one()
    if request.method == 'POST':
        reminder.owner = request.authenticated_userid
        reminder.title = request.params.get('title')
        reminder.payload = request.params.get('payload')
        reminder.delivery_time = request.params.get('delivery_time')
        return HTTPFound(request.route_url('list'))
    else:
        return {'reminder': reminder}


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

