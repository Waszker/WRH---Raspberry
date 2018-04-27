#!/bin/python2.7
import os
import signal

import tornado
import tornado.ioloop
import tornado.web
import tornado.gen
from tornado.tcpclient import TCPClient

from utils.decorators import log_exceptions
from utils.io import log, Color
from wrh_engine.tornado import resources

__UPLOADS__ = "/tmp/"
modules, classes = [], []
ip = None


class BaseHandler(tornado.web.RequestHandler):
    pass


class Userform(BaseHandler):
    @log_exceptions()
    def get(self):
        global modules, ip
        try:
            requested_module = self.get_argument("class")
            class_type_number = requested_module if requested_module in [c.WRHID for c in classes] else -1
        except tornado.web.MissingArgumentError:
            class_type_number = -1
        ip = str(self.request.host).split(":")[0]

        self.render("index.html", ipaddress=ip, target=class_type_number, classes=classes, modules=modules)


class Uptime(BaseHandler):
    @log_exceptions()
    def get(self):
        self.finish(resources.get_system_stats())


class Restart(BaseHandler):
    @log_exceptions()
    def get(self):
        self.finish(resources.restart())


class Request(BaseHandler):
    @tornado.gen.coroutine
    async def get(self):
        host = self.get_argument("host")
        port = int(self.get_argument("port"))
        message = self.get_argument("message")
        stream = await TCPClient().connect(host, port)
        if message:
            await stream.write(bytes(message))
        response = await stream.read_until_close()
        stream.close()
        self.finish(response)

    post = get


application = tornado.web.Application([
    (r"/", Userform),
    (r"/uptime", Uptime),
    (r"/restart", Restart),
    (r"/request", Request)
],
    debug=True,
    static_path=os.path.join(os.path.dirname("wrh_engine/tornado"), "tornado")
)


def sigint_handler(*_):
    tornado.ioloop.IOLoop.instance().stop()


if __name__ == "__main__":
    try:
        classes, modules = resources.get_installed_modules_info()
        signal.signal(signal.SIGINT, sigint_handler)
        application.listen(8888)
        log('Tornado: Started.')
        tornado.ioloop.IOLoop.instance().start()
    except Exception as e:
        log(e, Color.EXCEPTION)
