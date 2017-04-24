#!/bin/python2.7
import os
import sys
import tornado
import tornado.ioloop
import tornado.web
import resources
from utils.sockets import send_message, receive_message

__UPLOADS__ = "/tmp/"
modules = None
ip = None


class BaseHandler(tornado.web.RequestHandler):
    pass


class Userform(BaseHandler):
    def get(self):
        global modules, ip
        try:
            class_type_number = int(self.get_argument("class"))
        except (ValueError, tornado.web.MissingArgumentError):
            class_type_number = -1
        classes, modules = resources.get_available_module_types()
        ip = str(self.request.host).split(":")[0]

        self.render("index.html", ipaddress=ip, target=class_type_number, classes=classes, modules=modules)


class Uptime(BaseHandler):
    def get(self):
        self.finish(resources.get_system_stats())


class Restart(BaseHandler):
    def get(self):
        self.finish(resources.restart())


class Request(BaseHandler):
    def get(self):
        host = self.get_argument("host")
        port = self.get_argument("port")
        message = self.get_argument("message")
        self.finish(receive_message(host, port, message=message))

    def post(self):
        host = self.get_argument("host")
        port = self.get_argument("port")
        message = self.get_argument("message")
        self.finish(receive_message(host, port, message=message))


application = tornado.web.Application([
    (r"/", Userform),
    (r"/uptime", Uptime),
    (r"/restart", Restart),
    (r"/request", Request)
],
    debug=True,
    static_path=os.path.join(os.path.dirname("wrh_engine/tornado"), "tornado"))

if __name__ == "__main__":
    __CONFIG_FILE__ = sys.argv[1]
    application.listen(8888)
    print 'Tornado: Started.'
    tornado.ioloop.IOLoop.instance().start()
