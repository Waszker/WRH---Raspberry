import datetime
import json
import mimetypes
import os
import signal

import tornado
import tornado.ioloop
import tornado.web
import tornado.gen
from tornado.iostream import StreamClosedError
from tornado.tcpclient import TCPClient

from utils.decorators import log_exceptions
from utils.io import log, Color
from wrh_engine.tornado import resources

__UPLOADS__ = '/tmp/'
modules, classes = [], []
ip = None

# Serve the web app manifest with a proper type (older Pythons don't know this extension)
mimetypes.add_type('application/manifest+json', '.webmanifest')

# Time limits for talking to a module process (seconds). Reading may take a while, because some modules
# (e.g. Rango Iryga turning a line OFF) talk to a physical device before they close the connection.
MODULE_CONNECT_TIMEOUT = 3
MODULE_RESPONSE_TIMEOUT = 10


class BaseHandler(tornado.web.RequestHandler):
    pass


class Userform(BaseHandler):
    @log_exceptions()
    def get(self):
        global modules, ip
        try:
            requested_module = self.get_argument('class')
            class_type_number = requested_module if requested_module in [c.WRHID for c in classes] else -1
        except tornado.web.MissingArgumentError:
            class_type_number = -1
        ip = str(self.request.host).split(':')[0]

        self.render('index.html', ipaddress=ip, target=class_type_number, classes=classes, modules=modules)


class Uptime(BaseHandler):
    @log_exceptions()
    def get(self):
        # Tornado serializes dicts as JSON and sets the Content-Type header.
        self.finish(resources.get_system_stats())


class Restart(BaseHandler):
    @log_exceptions()
    def post(self):
        # Answer first, reboot a moment later so the browser gets the response (GET is rejected with 405)
        self.finish({'status': 'restarting'})
        tornado.ioloop.IOLoop.current().call_later(1, resources.restart)


class Request(BaseHandler):
    """
    Forwards a message to a module process listening on host:port and returns its response.
    Arguments (query string or form-encoded body): host (default: localhost), port, message.
    """

    async def post(self):
        host = self.get_argument('host', 'localhost')
        port = int(self.get_argument('port'))
        message = self.get_argument('message', '')
        stream = None
        try:
            # with_timeout zamiast connect(timeout=...), żeby działało też na Tornado < 5
            stream = await tornado.gen.with_timeout(
                datetime.timedelta(seconds=MODULE_CONNECT_TIMEOUT), TCPClient().connect(host, port))
            if message:
                await stream.write(message.encode('utf-8'))
            response = await tornado.gen.with_timeout(
                datetime.timedelta(seconds=MODULE_RESPONSE_TIMEOUT), stream.read_until_close(),
                quiet_exceptions=(StreamClosedError,))
        except tornado.gen.TimeoutError:
            return self._send_error(504, 'timeout')
        except (StreamClosedError, OSError):
            return self._send_error(502, 'connection_refused')
        finally:
            if stream is not None:
                stream.close()
        self._send_module_response(response)

    get = post

    def _send_error(self, status_code, error):
        self.set_status(status_code)
        self.finish({'error': error})

    def _send_module_response(self, response):
        try:
            json.loads(response.decode('utf-8'))
            self.set_header('Content-Type', 'application/json; charset=UTF-8')
        except ValueError:
            # Not JSON (older modules return plain text or HTML) - pass it through unchanged
            self.set_header('Content-Type', 'text/plain; charset=UTF-8')
        self.finish(response)


application = tornado.web.Application([
    (r'/', Userform),
    (r'/uptime', Uptime),
    (r'/restart', Restart),
    (r'/request', Request)
],
    debug=True,
    static_path=os.path.join(os.path.dirname('wrh_engine/tornado'), 'tornado')
)


def sigint_handler(*_):
    tornado.ioloop.IOLoop.instance().stop()


if __name__ == "__main__":
    try:
        classes, modules = resources.get_installed_modules_info()
        signal.signal(signal.SIGINT, sigint_handler)
        # WRH_WEB_PORT lets a second instance (e.g. a test checkout) run next to the production one
        web_port = int(os.environ.get('WRH_WEB_PORT', 8888))
        application.listen(web_port)
        log('Tornado: Started on port {}.'.format(web_port))
        tornado.ioloop.IOLoop.instance().start()
    except Exception as e:
        log(e, Color.EXCEPTION)
