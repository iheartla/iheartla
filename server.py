import tornado.ioloop
import tornado.web
import json
import os
import subprocess
import threading
from datetime import datetime
from app import process_input, read_from_file, save_to_file


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        # print("Received request: {}".format(data['input']))
        res = process_input(data['input'])
        self.set_header("Content-Type", "application/json")
        self.write(json.JSONEncoder().encode({"res": res}))
        # save updated markdown source to files
        s = threading.Thread(target=save_to_file, args=(data['input'], "./extras/resource/img/input-{}.md".format(datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))))
        s.start()


class FileHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        src = data['src']
        if data['type'] == "get":
        # print("Received request: {}".format(data['input']))
            res = read_from_file("./extras/resource/img/{}.py".format(src))
            self.set_header("Content-Type", "application/json")
            self.write(json.JSONEncoder().encode({"res": res}))
        elif data['type'] == "run":
            print("updated source: {}".format(data['source']))
            save_to_file(data['source'], "./extras/resource/img/{}.py".format(src))
            ret = subprocess.run(["python", "./extras/resource/img/{}.py".format(src)])
            if ret.returncode == 0:
                pass
                print("server succeed, {}".format(src))
            else:
                print("server failed, {}".format(src))
            self.write(json.JSONEncoder().encode({"ret": ret.returncode}))


def make_app():
    application = tornado.web.Application([
        (r"/handler", MainHandler),
        (r"/file", FileHandler),
        (r"/(.*)", tornado.web.StaticFileHandler, {"path": "./docs",
                                                   "default_filename": "index.html"})
    ], debug=True, autoreload=True)
    return application


if __name__ == "__main__":
    app = make_app()
    app.listen(8000)
    tornado.ioloop.IOLoop.current().start()

