from pyramid.config import Configurator
from sqlalchemy import engine_from_config
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
import os
from pyramid.security import Allow, ALL_PERMISSIONS, Authenticated

from .models import (
    DBSession,
    Base,
    )


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    auth_secret = os.environ.get('JOURNAL_AUTH_SECRET', 'itsaseekrit')
    config = Configurator(
        settings=settings,
        authentication_policy=AuthTktAuthenticationPolicy(
            secret=auth_secret,
            hashalg='sha512'
        ),
        authorization_policy=ACLAuthorizationPolicy(),
        root_factory='RootFactory'
    )
    config.include('pyramid_jinja2')
    config.add_static_view('static', 'static')
    config.add_route('home', '/')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('list', '/list')
    config.scan()
    return config.make_wsgi_app()

# this needs to be moved into models once we have them


class Reminder(object):
    @property
    def __acl__(self):
        return [
            (Allow, self.owner, 'edit')
            (Allow, 'group:admin', 'edit')
        ]


class RootFactory(object):
    __acl__ = [
        (Allow, 'group:admin', ALL_PERMISSIONS)
    ]


class ReminderFactory(object):
    __acl__ = [
        (Allow, Authenticated, 'create')
    ]