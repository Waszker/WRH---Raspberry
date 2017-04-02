#!/bin/python2.7
import os
import sys

import tornado
import tornado.ioloop
import tornado.web

import resources
from resources import getsystemstats

__UPLOADS__ = "/tmp/"
__CONFIG_FILE__ = ".wrh.config"
modules = None
ip = None


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")


class LoginHandler(BaseHandler):
    def get(self):
        self.render("login.html")

    def post(self):
        # Check if login and password are good
        input_name = self.get_argument("name")
        input_password = self.get_argument("password")
        if not input_name == "Name" or not input_password == "password":
            self.redirect("/login")
        else:
            # Password and login are good
            self.set_secure_cookie("user", self.get_argument("name"))
            self.redirect("/")


class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect("/login")


class Userform(BaseHandler):
    def get(self):
        isuservalid(self)
        global modules, ip
        try:
            class_type_number = int(self.get_argument("class"))
        except (ValueError, tornado.web.MissingArgumentError):
            class_type_number = -1
        classes, modules = resources.get_available_module_types(__CONFIG_FILE__)
        ip = str(self.request.host).split(":")[0]

        self.render("index.html", ipaddress=ip, target=class_type_number, classes=classes, modules=modules)


class Uptime(BaseHandler):
    def get(self):
        if not isuservalid(self): return
        self.finish(getsystemstats())


class Restart(BaseHandler):
    def get(self):
        if not isuservalid(self): return
        self.finish(resources.restart())


class Request(BaseHandler):
    def get(self):
        if not isuservalid(self): return
        host = self.get_argument("host")
        port = self.get_argument("port")
        message = self.get_argument("message")
        self.finish(resources.get_request(host, port, message))

    def post(self):
        if not isuservalid(self): return
        host = self.get_argument("host")
        port = self.get_argument("port")
        message = self.get_argument("message")
        resources.send_request(host, port, message)


application = tornado.web.Application([
    (r"/", Userform),
    (r"/login", LoginHandler),
    (r"/logout", LogoutHandler),
    (r"/uptime", Uptime),
    (r"/restart", Restart),
    (r"/request", Request)
],
    debug=True,
    cookie_secret="59711y60254197251521521",
    static_path=os.path.join(os.path.dirname("wrh_engine/tornado"), "tornado"))


def isuservalid(handler):
    if not handler.current_user:
        handler.redirect("/login")
        return False
    tornado.escape.xhtml_escape(handler.current_user)
    return True


if __name__ == "__main__":
    __CONFIG_FILE__ = sys.argv[1]
    application.listen(8888)
    print 'Tornado: Started.'
    tornado.ioloop.IOLoop.instance().start()
