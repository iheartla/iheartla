import argparse

import tornado.ioloop
import tornado.web
import json
import os
import sys
import subprocess
import threading
from datetime import datetime
from app import process_input, read_from_file, save_to_file, ParserTypeEnum
from iheartla.la_tools.la_msg import LaMsg
from pathlib import Path


default_input = ''
default_base = 'result'
default_path = '.'
def save_markdown(content):
    dst = "{}/input-history".format(default_path)
    if not os.path.exists(dst):
        os.mkdir(dst)
    save_to_file(content, "{}/input-history/input-{}.md".format(default_path, datetime.now().strftime("%Y-%m-%d-%H-%M-%S")))


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        # print("Received request: {}".format(data['input']))
        ret = 1
        extra_dict = {}
        try:
            res = process_input(data['input'], default_path, file_name=default_base, server_mode=True, parser_type=ParserTypeEnum.NUMPY)
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
        if data['type'] == "get":
            src = data['src']
            # print("Received request: {}".format(data['input']))
            res = read_from_file("{}/{}.py".format(default_path, src))
            self.set_header("Content-Type", "application/json")
            self.write(json.JSONEncoder().encode({"res": res}))
        elif data['type'] == "run":
            src = data['src']
            print("updated source: {}".format(data['source']))
            save_to_file(data['source'], "{}/{}.py".format(default_path, src))
            ret = subprocess.run(["python", "{}/img_code/{}.py".format(default_path, src)], cwd="{}/img_code".format(default_path))
            if ret.returncode == 0:
                pass
                print("server succeed, {}".format(src))
            else:
                print("server failed, {}".format(src))
            self.write(json.JSONEncoder().encode({"ret": ret.returncode}))
        elif data['type'] == "init":
            # initial input
            if default_input == '':
                ret = 1
            else:
                ret = 0
            self.write(json.JSONEncoder().encode({"ret": ret, "content": default_input}))


def make_app(custom_path):
    cur_path = os.path.dirname(os.path.abspath(__file__))
    application = tornado.web.Application([
        (r"/handler", MainHandler),
        (r"/file", FileHandler),
        (r"/heartdown-resource/(.*)", tornado.web.StaticFileHandler, {"path": "{}/extras/heartdown-resource".format(cur_path)}),
        (r"/css/(.*)", tornado.web.StaticFileHandler, {"path": "{}/docs/css".format(cur_path)}),
        (r"/js/(.*)", tornado.web.StaticFileHandler, {"path": "{}/docs/js".format(cur_path)}),
        (r"/icon/(.*)", tornado.web.StaticFileHandler, {"path": "{}/docs/icon".format(cur_path)}),
        (r"/fonts/(.*)", tornado.web.StaticFileHandler, {"path": "{}/docs/fonts".format(cur_path)}),
        (r"/(.*\.whl)", tornado.web.StaticFileHandler, {"path": "{}/docs".format(cur_path)}),
        (r"/(index\.html)", tornado.web.StaticFileHandler, {"path": "{}/docs".format(cur_path)}),
        (r"/()", tornado.web.StaticFileHandler, {"path": "{}/docs/index.html".format(cur_path),
                                                 "default_filename": "index.html"}),
        (r"/(.*)", tornado.web.StaticFileHandler, {"path": "{}".format(custom_path)})
    ], debug=True, autoreload=True)
    return application


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description='HeartDown local server')
    arg_parser.add_argument('paper', nargs='+', help='The paper source file to compile')
    args = arg_parser.parse_args()
    if args.paper:
        default_path = os.path.dirname(Path(args.paper[0]))
        default_base = os.path.splitext(os.path.basename(Path(args.paper[0])))[0]
        default_input = read_from_file(args.paper[0])
    app = make_app(default_path)
    app.listen(8000)
    print('Listening at http://localhost:8000/')
    tornado.ioloop.IOLoop.current().start()

