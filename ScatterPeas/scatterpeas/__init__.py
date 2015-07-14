from pyramid.config import Configurator
from sqlalchemy import engine_from_config
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
import os
from views import ReminderFactory, groupfinder, RootFactory

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
            hashalg='sha512',
            callback=groupfinder,
        ),
        authorization_policy=ACLAuthorizationPolicy(),
        root_factory=RootFactory
    )
    config.add_static_view('static', 'static')
    config.add_route('home', '/')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('list', '/list')
    config.add_route('detail_reminder', 'detailreminder/{title}', factory=ReminderFactory, traverse='/{title}')
    config.add_route('create_reminder', '/createreminder')
    config.add_route('edit_reminder', 'editreminder/{title}', factory=ReminderFactory, traverse='/{title}')
    config.scan()
    return config.make_wsgi_app()
