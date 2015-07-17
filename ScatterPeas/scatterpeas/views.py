from pyramid.response import Response
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPForbidden
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
import os
# from sqlalchemy.orm import scoped_session, sessoinmaker
# from zope.sqlalchemy import ZopeTransactionExtension
from cryptacular.bcrypt import BCRYPTPasswordManager
from pyramid.security import remember, forget
# from pyramid.security import Allow, ALL_PERMISSIONS, Authenticated
from dateutil import parser
import pytz
import scripts
import datetime

from .models import (
    DBSession,
    User,
    Alias,
    UUID,
    Reminder,
    RRule,
    Job
    )

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, 'scripts/gmail_creds.txt'), 'r') as fh:
    our_email = fh.readline()


# this needs to be moved into models once we have them


# class User(object):
#     @property
#     def __acl__(self):
#         return [
#             (Allow, self.username, 'edit'),
#             (Allow, 'group:admin', 'edit')
#         ]

#     def __init__(self, username, password, first_name=None, last_name=None,
#                  email=None, phone=None, default_medium='email',
#                  timezone='Pacific', groups=None):
#         self.username = username
#         self.password = password
#         self.first_name = first_name
#         self.last_name = last_name
#         self.email = email
#         self.phone = phone
#         self.default_medium = default_medium
#         self.timezone = timezone
#         self.groups = groups or []


# class Reminder(object):
#     @property
#     def __acl__(self):
#         return [
#             (Allow, self.owner, 'edit'),
#             (Allow, 'group:admin', ALL_PERMISSIONS)
#         ]

#     def __init__(self, owner, title, payload, delivery_time, method='email',
#                  email=None, phone=None):
#         self.owner = owner
#         self.title = title
#         self.payload = payload
#         self.delivery_time = delivery_time
#         self.method = method
#         self.email = email
#         self.phone = phone


# class Alias(object):
#     @property
#     def __acl__(self):
#         rule_list = []
#         for user in self.users:
#             rule_list.append((Allow, user.username, 'edit'))
#         rule_list.append((Allow, 'group:admin', ALL_PERMISSIONS))
#         return rule_list


# USERS = {}
# REMINDERS = {}
# USERS['user1'] = User('user1', 'password')
# USERS['user2'] = User('user2', 'password')
# USERS['admin'] = User('admin', 'password', groups=['admin'])
# REMINDERS['myreminder'] = Reminder('user1', 'myreminder', 'take out the garbage', 'a time')
# REMINDERS['reminder2'] = Reminder('user2', 'reminder2', 'feed the cat', 'time2')


# class RootFactory(object):
#     __acl__ = [
#         (Allow, 'group:admin', ALL_PERMISSIONS),
#         (Allow, Authenticated, 'create')
#     ]

#     def __init__(self, request):
#         self.request = request


# class ReminderFactory(object):
#     __acl__ = [
#         (Allow, 'group:admin', ALL_PERMISSIONS),
#     ]

#     def __init__(self, request):
#         self.request = request

#     def __getitem__(self, id):
#         return Reminder.retrieve_instance(id)


# class UserFactory(object):
#     __acl__ = [
#         (Allow, 'group:admin', ALL_PERMISSIONS)
#     ]

#     def __init__(self, request):
#         self.request = request

#     def __getitem__(self, username):
#         return User.by_username(username)


# class AliasFactory(object):
#     __acl__ = [
#         (Allow, 'group:admin', ALL_PERMISSIONS)
#     ]

#     def __init__(self, request):
#         self.request = request

#     def __getitem(self, id):
#         return Alias.by_id(id)


# def groupfinder(username, request):
#     user = User.by_username(username)
#     if user:
#         return ['group:%s' % g for g in user.groups]


def do_login(request):
    username = request.params.get('username', None)
    password = request.params.get('password', None)
    if not (username and password):
        raise ValueError('both username and password are required')

    return User.check_password(username, password)


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
            return HTTPFound(request.route_url('list'), headers=headers)

    return {'error': error, 'username': username}


@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(request.route_url('home'), headers=headers)


@view_config(route_name='list', renderer='templates/list.jinja2')
def list_reminders(request):
    if not request.authenticated_userid:
        return HTTPFound(request.route_url('login'))
    try:
        user = User.by_username(request.authenticated_userid)
    except NoResultFound:
        return HTTPFound(request.route_url('login'))
    reminders = []
    aliases = user.aliases
    for alias in aliases:
        for reminder in alias.reminders:
            reminders.append(reminder)
    return {'reminders': reminders}


@view_config(route_name='detail_reminder', renderer='templates/detail_reminder.jinja2', permission='edit')
def view_one_reminder(request):
    reminder = request.context
    return {'reminder': reminder}


def convert_to_naive_utc(delivery_time):
    dt = parser.parse(delivery_time)
    local = pytz.timezone("US/Pacific")
    local_dt = local.localize(dt)
    utc_dt = local_dt.astimezone(pytz.utc)
    naive_dt = utc_dt.replace(tzinfo=None)
    return naive_dt

@view_config(route_name='create_reminder', renderer='templates/create_reminder.jinja2', permission='create')
def create_reminder(request):
    username = request.authenticated_userid
    if request.method == 'POST':
        alias_id = request.params.get('alias_id')
        title = request.params.get('title')
        payload = request.params.get('payload')
        delivery_time = request.params.get('delivery_time')
        naive_dt = convert_to_naive_utc(delivery_time)
        reminder = Reminder.create_reminder(alias_id=alias_id, title=title,
            text_payload=payload)
        delivery_time = request.params.get('delivery_time')
        naive_dt = convert_to_naive_utc(delivery_time)
        rrule = RRule.create_rrule(reminder.id, naive_dt)
        reminder.rrule_id = rrule.id
        Reminder.parse_reminder(reminder.id)
        return HTTPFound(request.route_url('list'))
    else:
        all_aliases = User.get_aliases(username)
        aliases = []
        for alias in all_aliases:
            if alias.activation_state == 1:
                aliases.append(alias)
        return {'aliases': aliases}


@view_config(route_name='edit_reminder', renderer='templates/edit_reminder.jinja2', permission='edit')
def edit_reminder(request):
    reminder = request.context
    if request.method == 'POST':
        reminder.owner = request.authenticated_userid
        reminder.title = request.params.get('title')
        reminder.payload = request.params.get('payload')
        reminder.delivery_time = request.params.get('delivery_time')
        REMINDERS[reminder.title] = reminder
        return HTTPFound(request.route_url('list'))
    else:
        return {'reminder': reminder}


def send_confirmation_email(uuid, contact_info):
    title = "Your ScatterPeas confirmation link"
    msg = """\
Here's your confirmation link. Please click on it, or, if it's not \
highlighted, copy and paste it into your browser.

http://scatterpeas.com/confirm/{uuid}
""".format(uuid=uuid)
    scripts.gmail.send(our_email, contact_info, title, msg)


def send_confirmation_text(uuid, contact_info):
    msg = "Your ScatterPeas confirmation link: http://scatterpeas.com/confirm/{uuid}".format(uuid=uuid)
    scripts.send_sms.send_sms(msg, '+1{}'.format(contact_info), '+16319564194')


@view_config(route_name='create_user', renderer='templates/home.jinja2')
def create_user(request):
    error = ''
    if request.method == 'POST':
        username = request.params.get('username')
        password = request.params.get('password')
        first_name = request.params.get('first_name')
        last_name = request.params.get('last_name')
        contact_info = request.params.get('contact_info')
        default_medium = None
        if contact_info.isdigit():
            default_medium = 2
        else:
            default_medium = 1
        timezone = 'US/Pacific'
        try:
            user = User.create_user(username=username, password=password,
                first=first_name, last=last_name, dflt_medium=default_medium,
                timezone=timezone
            )
        except IntegrityError:
            error = "That username is taken."
            return {'error': error}
        alias = None
        uuid = None
        if default_medium == 1:
            alias = Alias.create_alias(user_id=user.id,
                contact_info=contact_info, medium=1
            )
            uuid = UUID.create_uuid(alias_id=alias.id)
            send_confirmation_email(uuid.uuid, alias.contact_info)
        elif default_medium == 2:
            alias = Alias.create_alias(user_id=user.id,
                contact_info=contact_info, medium=2
            )
            uuid = UUID.create_uuid(alias_id=alias.id)
            send_confirmation_text(uuid.uuid, alias.contact_info)
        UUID.email_sent(alias.id)
        return HTTPFound(request.route_url('wait_for_confirmation'))
    else:
        return {}


@view_config(route_name='wait_for_confirmation', renderer='templates/wait_for_confirmation.jinja2')
def wait_for_confirmation(request):
    return {}


@view_config(route_name='confirm_user', renderer='templates/confirm.jinja2')
def confirm_user(request):
    uuid = request.matchdict.get('uuid')
    alias_id, confirmation_state = UUID.get_alias(uuid)
    if confirmation_state == 1:
        Alias.activate(alias_id)
        UUID.success(uuid)
        message = "Success! You may now send reminders to this contact."
    elif confirmation_state == 2:
        message = "This address has already been confirmed."
    elif confirmation_state == -1:
        message = 'This confirmation link has expired.  Please try to confirm again.'
    return {'message': message}


@view_config(route_name='detail_user', renderer='templates/detail_user.jinja2', permission='edit')
def detail_user(request):
    user = request.context
    aliases = user.aliases
    return {'user': user, 'aliases': aliases}


@view_config(route_name='edit_user', renderer='templates/edit_user.jinja2', permission='edit')
def edit_user(request):
    user = request.context
    if request.method == 'POST':
        user.username = request.authenticated_userid
        password = request.params.get('password')
        manager = BCRYPTPasswordManager()
        hashed = manager.encode(password)
        user.password = hashed
        user.first_name = request.params.get('first_name')
        user.last_name = request.params.get('last_name')
        default_medium = request.params.get('default_medium').lower()
        if default_medium == 'email':
            user.dflt_medium = 1
        if default_medium == 'text':
            user.dflt_medium = 2
        else:
            raise ValueError()
        user.timezone = request.params.get('timezone')
        return HTTPFound(request.route_url('list'))
    else:
        return {'user': user}


@view_config(route_name='detail_alias', renderer='templates/detail_alias.jinja2', permission='edit')
def detail_alias(request):
    alias = request.context
    return {'alias': alias}


# @view_config(route_name='edit_alias', renderer='templates/edit_alias.jinja2', permission='edit')
# def edit_alias(request):
#     alias = request.context
#     if request.method == 'POST':
#         alias = request.params.get('alias')
#         contact_info = request.params.get('contact_info')
#         medium_text = request.params.get('medium')
#         medium = None
#         if medium_text == 'email':
#             medium = 1
#         if medium_text == 'text':
#             medium = 2
#         else:
#             raise ValueError()
#         activation_state = 0


@view_config(route_name='send_scheduled_mail', renderer='string')
def send_scheduled_mail(request):
    # query the database for scheduled jobs < cronjob interval
    jobs = Job.todo(5)
    message = "All jobs done.\n"
    for job in jobs:
        if job.job_state == 1:
            continue
        contact = job.reminder.alias.contact_info
        title = job.reminder.title
        payload = job.reminder.text_payload
        if job.reminder.alias.medium == 1:
            scripts.gmail.send(our_email, contact, title, payload)
            job.job_state = 1
            continue
        else:
            try:
                scripts.send_sms.send_sms(title, '+1{}'.format(contact), '+16319564194')
            except ValueError:
                message += "Failed to send job {}\n".format(title)
            else:
                job.job_state = 1
            continue
    return message


# @view_config(route_name='fetch_emails')
# def fetch_emails(request):
#     raw_email = receive()
#     # break up email into components
#     # create Reminder and write to database
#     pass


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
