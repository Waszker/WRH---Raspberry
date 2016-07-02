#!/bin/python2.7
import tornado
import tornado.ioloop
import tornado.web
import os
import sys
import resources
from resources import getsystemstats

__UPLOADS__ = "/tmp/"
__CONFIG_FILE__ = ".wrh.config"


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


class Userform(BaseHandler):
    def get(self):
        isuservalid(self)
        classes, self.modules = resources.get_available_module_types(__CONFIG_FILE__)
        self.ip = str(self.request.host).split(":")[0]

        self.render("index.html", classes=classes, modules=self.modules)


class Uptime(BaseHandler):
    def get(self):
        if not isuservalid(self): return
        self.finish(getsystemstats())


class GetPage(BaseHandler):
    def get(self):
        if not isuservalid(self): return
        class_type_number = int(self.get_argument("class"))
        if class_type_number == -1:
            # TODO: Finish index.html content here
            content = ""
        else:
            modules = resources.get_modules_with_type_number(class_type_number, self.modules)
            content = resources.get_page_content_for_modules(self.ip, modules)
        self.finish(content)


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
    (r"/uptime", Uptime),
    (r"/page", GetPage),
    (r"/request", Request)
],
    debug=True,
    cookie_secret="59711y60254197251521521",
    static_path=os.path.join(os.path.dirname("WRH_Engine/Modules/TORNADO"), "TORNADO"))


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
