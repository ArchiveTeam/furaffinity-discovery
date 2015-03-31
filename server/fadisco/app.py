import json

from tornado.web import URLSpec as U
import tornado.web


class App(tornado.web.Application):
    def __init__(self, model, prefix=''):
        handlers = [
            U(prefix + r'/api/user_discovery', UserDiscoveryHandler),
            U(prefix + r'/api/user_private_discovery', UserPrivateDiscoveryHandler),
            U(prefix + r'/api/get_secrets', GetSecretsHandler),
        ]

        super(App, self).__init__(handlers)
        self.model = model


class BaseHandler(tornado.web.RequestHandler):
    pass


class UserDiscoveryHandler(BaseHandler):
    def post(self):
        try:
            doc = json.loads(self.request.body.decode('ascii'))
        except (ValueError, UnicodeError):
            raise tornado.web.HTTPError(400)

        self.application.model.add_user_discovery(doc)


class UserPrivateDiscoveryHandler(BaseHandler):
    def post(self):
        try:
            doc = json.loads(self.request.body.decode('ascii'))
        except (ValueError, UnicodeError):
            raise tornado.web.HTTPError(400)

        self.application.model.add_user_private_discovery(doc)


class GetSecretsHandler(BaseHandler):
    def post(self):
        version = self.get_argument('v')

        if version != '1':
            raise tornado.web.HTTPError(400)

        self.write(self.application.get_secrets(self.request.remote_ip))
