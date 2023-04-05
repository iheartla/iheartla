from .la_helper import *
from .la_logger import *
from .la_package import * 
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
import regex as re
from datetime import datetime

class CacheModuleData(object):
    def __init__(self, name='', timestamp='', parser_type='', pre_frame=None, type_walker=None):
        super().__init__()
        self.name = name                 # module name
        self.timestamp = timestamp       # timestamp 
        self.parser_type = parser_type   # parser type 
        self.type_walker = type_walker
        self.pre_frame = pre_frame
    

class CacheModuleManager(object):
    __instance = None
    @staticmethod
    def getInstance():
        if CacheModuleManager.__instance is None:
            CacheModuleManager()
        return CacheModuleManager.__instance

    def __init__(self):
        if CacheModuleManager.__instance is not None:
            raise Exception("Class CacheModuleManager is a singleton!")
        self.module_cache_dir = os.path.join(user_cache_dir(), "iheartmesh_modules")    # local cache folder
        self.init_cache()
        self.cache_module_dict = {}   # saved data
        self.load_cached_modules()
        CacheModuleManager.__instance = self
        
    def get_compiled_module(module_name, parser_type, timestamp):
        tmp_type_walker = None
        pre_frame = None
        return tmp_type_walker, pre_frame
    
    def save_compiled_module(self, type_walker, pre_frame, module_name, parser_type, timestamp):
        data = {"walker": type_walker,
                "frame": pre_frame}
        data_file = Path(self.module_cache_dir + "/{}_{}_{}.pickle".format(module_name, parser_type, timestamp))
        # write data 
        try:
            with open(data_file, 'wb') as f:
                pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            print("IO error:{}".format(e))
    
    def load_cached_modules(self):
        for f in listdir(self.module_cache_dir):
            if self.valid_module_cache(f):
                pure_name = f.replace(".pickle", "")
                module_name, parser_type, timestamp = pure_name.split('_')
                print("module_name:{}, parser:{}, timestamp:{}".format(module_name, parser_type, timestamp))
                try:
                    with open(Path(self.module_cache_dir + "/" + f), 'rb') as ff:
                        data_dict = pickle.load(ff)
                        self.cache_module_dict[module_name] = CacheModuleData(name=module_name, timestamp=timestamp, parser_type=parser_type, pre_frame=data_dict["frame"], type_walker = data_dict["walker"])
                except Exception as e:
                    print("IO error:{}".format(e))
    
    def valid_module_cache(self, cache_file):
        return '.pickle' in cache_file and '_' in cache_file
    
    def init_cache(self):
        # cache dir may not exist yet
        if not Path(user_cache_dir()).exists():
            Path(user_cache_dir()).mkdir()
        # real cached dir
        dir_path = Path(self.module_cache_dir)
        if not dir_path.exists():
            dir_path.mkdir() 
    
    