import tornado.ioloop
import tornado.web
import os
from app import process_input


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")


def make_app():
    application = tornado.web.Application([
        (r"/(.*)", tornado.web.StaticFileHandler, {"path": "./docs",
                                                   "default_filename": "index.html"})
    ])
    return application


if __name__ == "__main__":
    app = make_app()
    app.listen(8000)
    tornado.ioloop.IOLoop.current().start()

