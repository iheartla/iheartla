from la_tools.la_helper import *
from la_tools.la_logger import *
import pickle
import tatsu
import time
from appdirs import *
from os import listdir
from pathlib import Path
import hashlib
import importlib
import threading
MAXIMUM_SIZE = 12  # 10 + 2 default


class ParserManager(object):
    def __init__(self):
        self.logger = LaLogger.getInstance().get_logger(LoggerTypeEnum.DEFAULT)
        self.parser_dict = {}
        self.prefix = "grammar"
        self.module_dir = "la_local_parsers"
        self.default_parsers = [hashlib.md5("init".encode()).hexdigest(), hashlib.md5("default".encode()).hexdigest()]
        # create the user's cache directory (pickle)
        # self.cache_dir = user_cache_dir("iheartla")
        # dir_path = Path(self.cache_dir)
        # if not dir_path.exists():
        #     dir_path.mkdir()
        # self.cache_file = Path(self.cache_dir + '/parsers.pickle')
        #######
        self.load_parsers()

    def load_from_pickle(self):
        # Load parsers when program launches
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'rb') as f:
                    self.parser_dict = pickle.load(f)
            except Exception as e:
                print("IO error:{}".format(e))

    def load_parsers(self):
        for f in listdir(self.module_dir):
            if self.prefix in f and '.py' in f and '_' in f:
                name = f.split('.')[0]
                hash_value = name.split('_')[1]
                module_name = "la_local_parsers.{}".format(name)
                module = importlib.import_module(module_name)
                parser_a = getattr(module, "grammar{}Parser".format(hash_value))
                parser_semantic = getattr(module, "grammar{}ModelBuilderSemantics".format(hash_value))
                parser = parser_a(semantics=parser_semantic())
                self.parser_dict[hash_value] = parser
        self.logger.debug("After loading, self.parser_dict:{}".format(self.parser_dict))
        if len(self.parser_dict) > 1:
            print("{} parsers loaded".format(len(self.parser_dict)))
        else:
            print("{} parser loaded".format(len(self.parser_dict)))

    def get_parser(self, key, grammar):
        hash_value = hashlib.md5(key.encode()).hexdigest()
        if hash_value in self.parser_dict:
            return self.parser_dict[hash_value]
        # os.path.dirname(filename) is used as the prefix for relative #include commands
        # It just needs to be a path inside the directory where all the grammar files are.
        parser = tatsu.compile(grammar, asmodel=True, filename='la_grammar/here')
        self.parser_dict[hash_value] = parser
        # save to file asynchronously
        save_thread = threading.Thread(target=self.save_grammar, args=(hash_value, grammar,))
        save_thread.start()
        # self.save_dict()
        return parser

    def save_grammar(self, hash_value, grammar):
        self.check_parser_cnt()
        code = tatsu.to_python_sourcecode(grammar, name="grammar{}".format(hash_value), filename='la_grammar/here')
        code_model = tatsu.to_python_model(grammar, name="grammar{}".format(hash_value), filename='la_grammar/here')
        code_model = code_model.replace("from __future__ import print_function, division, absolute_import, unicode_literals", "")
        code += code_model
        save_to_file(code, "{}/grammar_{}.py".format("la_local_parsers", hash_value))

    def check_parser_cnt(self):
        parser_size = len(self.parser_dict)
        self.logger.debug("check_parser_cnt, self.parser_dict:{}, max:{}".format(self.parser_dict, MAXIMUM_SIZE))
        while parser_size > MAXIMUM_SIZE:
            earliest_time = time.time()
            earliest_file = None
            earliest_hash = None
            for f in listdir(self.module_dir):
                if self.prefix in f and '.py' in f and '_' in f:
                    name = f.split('.')[0]
                    hash_value = name.split('_')[1]
                    if hash_value not in self.default_parsers:
                        cur_time = os.path.getmtime(self.module_dir + '/' + f)
                        if cur_time < earliest_time:
                            earliest_time = cur_time
                            earliest_file = f
                            earliest_hash = hash_value
            if earliest_file is not None and earliest_hash in self.parser_dict:
                del self.parser_dict[earliest_hash]
                os.remove(self.module_dir + '/' + earliest_file)
                parser_size = len(self.parser_dict)
            else:
                 break
        self.logger.debug("check_parser_cnt, self.parser_dict:{}".format(self.parser_dict))

    def save_dict(self):
        self.logger.debug("self.parser_dict:{}".format(self.parser_dict))
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.parser_dict, f, pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            print("IO error:{}".format(e))

