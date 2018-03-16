#!/bin/python2.7
import os
import signal

import tornado
import tornado.ioloop
import tornado.web

import resources
from utils.decorators import log_exceptions
from utils.io import log, Color
from utils.sockets import receive_message

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
    @log_exceptions()
    def get(self):
        host = self.get_argument("host")
        port = self.get_argument("port")
        message = self.get_argument("message")
        self.finish(receive_message(host, port, message=message))

    @log_exceptions()
    def post(self):
        host = self.get_argument("host")
        port = self.get_argument("port")
        message = self.get_argument("message")
        self.finish(receive_message(host, port, message=message, buffer_size=1024 * 1024))


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
        print 'Tornado: Started.'
        tornado.ioloop.IOLoop.instance().start()
    except Exception as e:
        log(e, Color.EXCEPTION)
