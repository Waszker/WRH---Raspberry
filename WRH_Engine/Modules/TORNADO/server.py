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
        items = []
        cameraPorts = resources.get_camera_streaming_ports(__CONFIG_FILE__)
        sockets = resources.get_sockets(__CONFIG_FILE__)
        ip = str(self.request.host).split(":")[0]
        for file in os.listdir(__UPLOADS__):
            items.append(file)

        self.render("index.html", items=items, ipaddress=ip, cameraPorts = cameraPorts, sockets = sockets)

class Upload(BaseHandler):
    def post(self):
        if isuservalid(self) == False: return
        fileinfo = self.request.files['filearg'][0]
        print ('fileinfo is ', fileinfo)
        # fname = fileinfo['filename']
        # extn = os.path.splitext(fname)[1]
        # cname = str(uuid.uuid4()) + extn
        fh = open(__UPLOADS__ + fileinfo['filename'], 'w')
        fh.write(fileinfo['body'])
        self.finish(fileinfo['filename'] + " is uploaded!! Check %s folder" %__UPLOADS__)

class Show(BaseHandler):
    def get(self):
        if isuservalid(self) == False: return
        filename = self.get_argument("filename", default=None, strip=False)
        fh = open(__UPLOADS__ + filename, 'r')
        self.finish(fh.read())

class Uptime(BaseHandler):
    def get(self):
        if isuservalid(self) == False: return
        self.finish(getsystemstats())

class Socket(BaseHandler):
    def get(self):
        if isuservalid(self) == False: return
        id = self.get_argument("number")
        self.finish(resources.getelectricalsocketstate(__CONFIG_FILE__, id))

    def post(self):
        if isuservalid(self) == False: return
        state = self.get_argument("state")
        id = self.get_argument("number")
        resources.setelectrcalsocketstate(__CONFIG_FILE__, id, state)

application = tornado.web.Application([
    (r"/", Userform),
    (r"/login", LoginHandler),
    (r"/upload", Upload),
    (r"/show", Show),
    (r"/uptime", Uptime),
    (r"/socket", Socket),
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
