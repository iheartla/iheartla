import tornado.ioloop
import tornado.web
import json
import os
from app import process_input


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        print("Received request: {}".format(data['input']))
        res = process_input(data['input'])
        self.set_header("Content-Type", "application/json")
        self.write(json.JSONEncoder().encode({"res": res}))


def make_app():
    application = tornado.web.Application([
        (r"/handler", MainHandler),
        (r"/(.*)", tornado.web.StaticFileHandler, {"path": "./docs",
                                                   "default_filename": "index.html"})
    ], debug=True, autoreload=True)
    return application


if __name__ == "__main__":
    app = make_app()
    app.listen(8000)
    tornado.ioloop.IOLoop.current().start()

