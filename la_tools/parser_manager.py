from .la_helper import *
from .la_logger import *
import pickle
import tatsu
import time
from appdirs import *
from os import listdir
from pathlib import Path
import hashlib
import importlib
import importlib.util
import threading
import shutil
from datetime import datetime


class ParserManager(object):
    def __init__(self, grammar_dir):
        self.grammar_dir = Path(grammar_dir)
        self.max_size = 12  # 10 + 2 default
        self.logger = LaLogger.getInstance().get_logger(LoggerTypeEnum.DEFAULT)
        self.parser_dict = {}
        self.prefix = "parser"
        self.module_dir = "iheartla"
        self.default_parsers_dict = {hashlib.md5("init".encode()).hexdigest(): 0, hashlib.md5("default".encode()).hexdigest(): 0}
        for f in (self.grammar_dir.parent / 'la_local_parsers').glob('parser*.py'):
            name, hash_value, t = self.separate_parser_file(f.name)
            if hash_value in self.default_parsers_dict:
                self.default_parsers_dict[hash_value] = t
        self.save_threads = []
        # create the user's cache directory (pickle)
        self.cache_dir = os.path.join(user_cache_dir(), self.module_dir)
        # init the cache and load the default parsers
        self.init_cache()
        self.load_parsers()
    
    def reload(self):
        self.parser_dict = {}
        self.init_cache()
        self.load_parsers()

    def set_test_mode(self):
        self.max_size = 1000

    def separate_parser_file(self, parser_file):
        """
        :param parser_file: parser_****_****.py
        :return: full_file_name, hash_value, timestamp
        """
        name = parser_file.split('.')[0]
        sep_list = name.split('_')
        timestamp = time.mktime(datetime.strptime(sep_list[2], "%Y-%m-%d-%H-%M-%S").timetuple())
        return name, sep_list[1], timestamp

    def merge_default_parsers(self):
        # dir has been created
        copy_from_default = True
        for f in listdir(self.cache_dir):
            if self.valid_parser_file(f):
                name, hash_value, t = self.separate_parser_file(f)
                if hash_value in self.default_parsers_dict:
                    if self.default_parsers_dict[hash_value] <= t:
                        copy_from_default = False
                        break
        if copy_from_default:
            # remove all current parsers
            self.clean_parsers()
            # copy default parsers
            dir_path = Path(self.cache_dir)
            for f in (self.grammar_dir.parent/'la_local_parsers').glob('parser*.py'):
                if not (dir_path/f.name).exists():
                    shutil.copy(f, dir_path)

    def valid_parser_file(self, parser_file):
        return self.prefix in parser_file and '.py' in parser_file and '_' in parser_file

    def init_cache(self):
        # cache dir may not exist yet
        if not Path(user_cache_dir()).exists():
            Path(user_cache_dir()).mkdir()
        # real dir
        dir_path = Path(self.cache_dir)
        if not dir_path.exists():
            dir_path.mkdir()
        self.merge_default_parsers()
        # self.cache_file = Path(self.cache_dir + '/parsers.pickle')

    def clean_parsers(self):
        dir_path = Path(self.cache_dir)
        if dir_path.exists():
            shutil.rmtree(dir_path)
            dir_path.mkdir()

    def load_from_pickle(self):
        # Load parsers when program launches
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'rb') as f:
                    self.parser_dict = pickle.load(f)
            except Exception as e:
                print("IO error:{}".format(e))

    def load_parsers(self):
        for f in listdir(self.cache_dir):
            if self.valid_parser_file(f):
                name, hash_value, t = self.separate_parser_file(f)
                module_name = "{}.{}".format(self.module_dir, name)
                path_to_file = os.path.join(self.cache_dir, "{}.py".format(name))
                spec = importlib.util.spec_from_file_location(module_name, path_to_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
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
        parser = tatsu.compile(grammar, asmodel=True)
        self.parser_dict[hash_value] = parser
        try:
            # save to file asynchronously
            save_thread = threading.Thread(target=self.save_grammar, args=(hash_value, grammar,))
            save_thread.start()
            self.save_threads.append( save_thread )
        except:
            self.save_grammar(hash_value, grammar)
        # self.save_dict()
        return parser

    def save_grammar(self, hash_value, grammar):
        self.check_parser_cnt()
        code = tatsu.to_python_sourcecode(grammar, name="grammar{}".format(hash_value), filename=os.path.join('la_grammar', 'here'))
        code_model = tatsu.to_python_model(grammar, name="grammar{}".format(hash_value), filename=os.path.join('la_grammar', 'here'))
        code_model = code_model.replace("from __future__ import print_function, division, absolute_import, unicode_literals", "")
        code += code_model
        save_to_file(code, os.path.join(self.cache_dir, "{}_{}_{}.py".format(self.prefix, hash_value, datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))))

    def check_parser_cnt(self):
        parser_size = len(self.parser_dict)
        self.logger.debug("check_parser_cnt, self.parser_dict:{}, max:{}".format(self.parser_dict, self.max_size))
        while parser_size > self.max_size:
            earliest_time = time.time()
            earliest_file = None
            earliest_hash = None
            for f in listdir(self.cache_dir):
                if self.valid_parser_file(f):
                    name, hash_value, t = self.separate_parser_file(f)
                    if hash_value not in self.default_parsers_dict:
                        cur_time = os.path.getmtime(os.path.join(self.cache_dir, f))
                        if cur_time < earliest_time:
                            earliest_time = cur_time
                            earliest_file = f
                            earliest_hash = hash_value
            if earliest_file is not None and earliest_hash in self.parser_dict:
                del self.parser_dict[earliest_hash]
                os.remove(os.path.join(self.cache_dir, earliest_file))
                parser_size = len(self.parser_dict)
            else:
                # avoid dead loop
                break
        self.logger.debug("check_parser_cnt, self.parser_dict:{}".format(self.parser_dict))

    def save_dict(self):
        self.logger.debug("self.parser_dict:{}".format(self.parser_dict))
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.parser_dict, f, pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            print("IO error:{}".format(e))


def recreate_local_parser_cache():
    ### WARNING: This will delete and re-create the cache and 'la_local_parsers' directories.
    import la_parser.parser
    PM = la_parser.parser._parser_manager
    
    print( '## Clearing the cache dir:', PM.cache_dir )
    shutil.rmtree( PM.cache_dir )
    Path(PM.cache_dir).mkdir()
    
    la_local_parsers = PM.grammar_dir.parent/'la_local_parsers'
    print( '## Clearing the la_local_parsers dir:', la_local_parsers )
    shutil.rmtree( la_local_parsers )
    la_local_parsers.mkdir()
    
    print('## Reloading the ParserManager.')
    PM.reload()
    
    print('## Re-creating the parsers.')
    la_parser.parser.create_parser()
    
    print('## Waiting for them to be saved.')
    for thread in PM.save_threads: thread.join()
    
    print('## Copying the cache dir contents into the local dir.')
    for f in Path(PM.cache_dir).glob('*.py'):
        shutil.copy( f, la_local_parsers )
    
    print('## Done.')
