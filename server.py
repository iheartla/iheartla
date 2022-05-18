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
from iheartla.la_tools.la_helper import *
from pathlib import Path


default_input = ''
default_base = 'result'
default_path = '.'
def save_markdown(content):
    dst = "{}/{}".format(default_path, INPUT_HISTORY)
    if not os.path.exists(dst):
        os.makedirs(dst)
    # Overwrite the input file
    if not DEBUG_MODE:
        save_to_file(content, "{}/{}.md".format(default_path, default_base))
    # Save a backup
    save_to_file(content, "{}/{}/{}-{}.md".format(default_path, INPUT_HISTORY, default_base, datetime.now().strftime("%Y-%m-%d-%H-%M-%S")))


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        # print("Received request: {}".format(data['input']))
        ret = 1
        extra_dict = {}
        figure_dict = {}
        if DEBUG_MODE:
            res, figure_dict = process_input(data['input'], default_path, file_name=default_base, server_mode=True)
            ret = 0
            extra_dict["res"] = res
            extra_dict["ret"] = ret
            extra_dict["name"] = default_base
            # print(figure_dict)
            if len(figure_dict) > 0:
                extra_dict["fig"] = figure_dict
        else:
            try:
                res, figure_dict = process_input(data['input'], default_path, file_name=default_base, server_mode=True)
                ret = 0
                extra_dict["res"] = res
                extra_dict["name"] = default_base
            except AssertionError as e:
                err_msg = LaMsg.getInstance()
                extra_dict["expr"] = err_msg.cur_code.replace('\n', '')
                extra_dict["msg"] = err_msg.cur_msg
            except Exception as e:
                extra_dict["msg"] = "{}: {}".format(type(e).__name__, str(e))
            except:
                extra_dict["msg"] = str(sys.exc_info()[0])
            finally:
                extra_dict["ret"] = ret
                if len(figure_dict) > 0:
                    extra_dict["fig"] = figure_dict
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
            res = read_from_file("{}/{}/{}.py".format(default_path, IMG_CODE, src))
            self.set_header("Content-Type", "application/json")
            self.write(json.JSONEncoder().encode({"res": res}))
        elif data['type'] == "run":
            src = data['src']
            # print("updated source: {}".format(data['source']))
            save_to_file(data['source'], "{}/{}.py".format(default_path, src))
            ret = subprocess.run(["python", "{}/{}/{}.py".format(default_path, IMG_CODE, src)],
                                 cwd="{}/{}".format(default_path, IMG_CODE),
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if ret.returncode == 0:
                pass
                print("server succeed, {}".format(src))
            else:
                print("server failed, {}".format(src))
            self.write(json.JSONEncoder().encode({"ret": ret.returncode, "msg": ret.stderr.decode('UTF-8')}))
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
        default_path = os.path.abspath(default_path)
        # The following is equivalent to: default_base = Path(args.paper[0]).stem
        default_base = os.path.splitext(os.path.basename(Path(args.paper[0])))[0]
        default_input = read_from_file(args.paper[0])
    
    # save the contents into the backup folder
    save_markdown(default_input)
    
    app = make_app(default_path)
    app.listen(8000)
    print('Listening at http://localhost:8000/')
    if not DEBUG_MODE:
        import webbrowser
        webbrowser.open('http://localhost:8000/')
    tornado.ioloop.IOLoop.current().start()

