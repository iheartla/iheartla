import tornado.ioloop
import tornado.web
import json
import os
import sys
import subprocess
import threading
from datetime import datetime
from app import process_input, read_from_file, save_to_file, get_resource_dir
from iheartla.la_tools.la_msg import LaMsg


def save_markdown(content):
    dst = "{}/input-history".format(get_resource_dir())
    if not os.path.exists(dst):
        os.mkdir(dst)
    save_to_file(content, "{}/input-history/input-{}.md".format(get_resource_dir(), datetime.now().strftime("%Y-%m-%d-%H-%M-%S")))


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        # print("Received request: {}".format(data['input']))
        ret = 1
        extra_dict = {}
        try:
            res = process_input(data['input'], server_mode=True)
            ret = 0
            extra_dict["res"] = res
        except AssertionError as e:
            err_msg = LaMsg.getInstance()
            extra_dict["expr"] = err_msg.cur_code.replace('\n', '')
            extra_dict["msg"] = err_msg.cur_msg
        except Exception as e:
            extra_dict["msg"] = str(e)
        except:
            extra_dict["msg"] = str(sys.exc_info()[0])
        finally:
            extra_dict["ret"] = ret
        self.set_header("Content-Type", "application/json")
        self.write(json.JSONEncoder().encode(extra_dict))
        # save updated markdown source to files
        s = threading.Thread(target=save_markdown, args=(data['input'],))
        s.start()


class FileHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        src = data['src']
        if data['type'] == "get":
        # print("Received request: {}".format(data['input']))
            res = read_from_file("{}/{}.py".format(get_resource_dir(), src))
            self.set_header("Content-Type", "application/json")
            self.write(json.JSONEncoder().encode({"res": res}))
        elif data['type'] == "run":
            print("updated source: {}".format(data['source']))
            save_to_file(data['source'], "{}/{}.py".format(get_resource_dir(), src))
            ret = subprocess.run(["python", "{}/{}.py".format(get_resource_dir(), src)])
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

