from .la_helper import *
from .la_logger import *
from .la_package import *
if not DEBUG_PARSER:
    from ..la_local_parsers.init_parser import grammarinitParser, grammarinitModelBuilderSemantics
    from ..la_local_parsers.default_parser import grammardefaultParser, grammardefaultModelBuilderSemantics
    # from ..la_local_parsers.config_parser import grammarconfigParser, grammarconfigModelBuilderSemantics
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

class ParserManager(object):
    __instance = None
    @staticmethod
    def getInstance(grammar_dir=''):
        if ParserManager.__instance is None:
            ParserManager(grammar_dir)
        return ParserManager.__instance

    def __init__(self, grammar_dir):
        if ParserManager.__instance is not None:
            raise Exception("Class ParserManager is a singleton!")
        else:
            if DEBUG_PARSER:
                self.parser_file_manager = ParserFileManager(grammar_dir)
                self.cache_dir = self.parser_file_manager.cache_dir
                self.grammar_dir = self.parser_file_manager.grammar_dir
                self.save_threads = self.parser_file_manager.save_threads
            else:
                self.init_parser = grammarinitParser(semantics=grammarinitModelBuilderSemantics())
                self.default_parser = grammardefaultParser(semantics=grammardefaultModelBuilderSemantics())
                # disable # as comment symbol 
                # https://github.com/neogeny/TatSu/issues/293
                # https://github.com/neogeny/TatSu/issues/249
                init_parser_config = getattr(self.init_parser, "config", None)
                if init_parser_config:
                    # Work around BC break in Tatsu 5.7
                    init_parser_config.comments_re = None
                    init_parser_config.eol_comments_re = None
                ast_parser_config = getattr(self.default_parser, "config", None)
                if ast_parser_config:
                    # Work around BC break in Tatsu 5.7
                    ast_parser_config.comments_re = None
                    ast_parser_config.eol_comments_re = None
                # self.config_parser = grammarconfigParser(semantics=grammarconfigModelBuilderSemantics())
            ParserManager.__instance = self

    def get_parser(self, key, grammar, extra_dict={}):
        if DEBUG_PARSER:
            return self.parser_file_manager.get_parser(key, grammar, extra_dict)
        else:
            if key == 'init':
                return self.init_parser
            # elif key == 'config':
            #     return self.config_parser
            self.modify_default_parser(extra_dict)
            return self.default_parser

    def create_config_parser(self):
        if DEBUG_PARSER:
            from ..de_companion.config_ebnf import CONFIG
            self.get_parser('config', CONFIG)

    def set_test_mode(self):
        if DEBUG_PARSER:
            self.parser_file_manager.set_test_mode()

    def reload(self):
        if DEBUG_PARSER:
            self.parser_file_manager.reload()

    def modify_default_parser(self, extra_dict):
        self.default_parser.new_id_list = []
        self.default_parser.new_func_list = []
        self.default_parser.builtin_list = []
        self.default_parser.conversion_dict = {}
        self.default_parser.const_e = False
        if "ids" in extra_dict:
            self.default_parser.new_id_list = extra_dict["ids"]
            la_debug("Modify default parser, ids:{}".format(extra_dict["ids"]))
        if 'funcs' in extra_dict:
            self.default_parser.new_func_list = extra_dict["funcs"]
            la_debug("Modify default parser, funcs:{}".format(extra_dict["funcs"]))
        if 'pkg' in extra_dict:
            funcs_list = extra_dict["pkg"]
            if 'e' in funcs_list:
                self.default_parser.const_e = True
                funcs_list.remove('e')
            self.default_parser.builtin_list = funcs_list
            la_debug("Modify default parser, pkg:{}".format(extra_dict["pkg"]))
        if 'rename' in extra_dict:
            self.default_parser.conversion_dict = extra_dict["rename"]
            la_debug("Modify default parser, rename:{}".format(extra_dict["rename"]))


class ParserFileManager(object):
    def __init__(self, grammar_dir):
        self.grammar_dir = Path(grammar_dir)
        self.max_size = 12  # 10 + 2 default
        self.logger = LaLogger.getInstance().get_logger(LoggerTypeEnum.DEFAULT)
        self.parser_dict = {}
        self.prefix = "parser"
        self.module_dir = "iheartla"
        self.default_hash_value = hashlib.md5("default".encode()).hexdigest()
        self.init_hash_value = hashlib.md5("init".encode()).hexdigest()
        self.config_hash_value = hashlib.md5("config".encode()).hexdigest()
        self.default_parsers_dict = {self.init_hash_value: 0, self.default_hash_value: 0, self.config_hash_value: 0}
        for f in (self.grammar_dir.parent / 'la_local_parsers').glob('parser*.py'):
            name, hash_value, t = self.separate_parser_file(f.name)
            if hash_value in self.default_parsers_dict:
                self.default_parsers_dict[hash_value] = t
                if hash_value == self.default_hash_value:
                    default_file = open(grammar_dir / f)
                    self.default_parser_content = default_file.read()
                    default_file.close()
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

    def get_parser(self, key, grammar, extra_dict={}):
        hash_value = hashlib.md5(key.encode()).hexdigest()
        if hash_value in self.parser_dict:
            return self.parser_dict[hash_value]
        if not DEBUG_PARSER:
            # create new parser from default parser
            rule_content = self.gen_parser_code(hash_value, extra_dict)
            module_name = "{}_{}_{}".format(self.prefix, hash_value, datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
            new_file_name = os.path.join(self.cache_dir, "{}.py".format(module_name))
            save_to_file(rule_content, new_file_name)
            # load new parser
            spec = importlib.util.spec_from_file_location(module_name, new_file_name)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            parser_a = getattr(module, "grammar{}Parser".format(hash_value))
            parser_semantic = getattr(module, "grammar{}ModelBuilderSemantics".format(hash_value))
            parser = parser_a(semantics=parser_semantic())
            self.parser_dict[hash_value] = parser
            return parser
        else:
            # os.path.dirname(filename) is used as the prefix for relative #include commands
            # It just needs to be a path inside the directory where all the grammar files are.
            parser = tatsu.compile(grammar, asmodel=True)
            self.parser_dict[hash_value] = parser
            try:
                # save to file asynchronously
                # print("hash_value is:{}, grammar:{}".format(hash_value, grammar))
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
        # code_model = code_model.replace("from __future__ import print_function, division, absolute_import, unicode_literals", "")
        code_model = code_model.replace("from __future__ import annotations", "")
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

    def gen_parser_code(self, hash_value, extra_dict):
        cur_content = self.default_parser_content.replace(self.default_hash_value, hash_value)
        if "ids" in extra_dict:
            id_list = extra_dict["ids"]
            id_alone_original_rule = r"""class IdentifierAlone(ModelBase):
    id = None
    value = None"""
            id_alone_cur_rule = r"""class IdentifierAlone(ModelBase):
    const = None
    id = None
    value = None"""
            cur_content = cur_content.replace(id_alone_original_rule, id_alone_cur_rule)
            id_original_rule = r"""@tatsumasu('IdentifierAlone')
    def _identifier_alone_(self):  # noqa
        with self._ifnot():
            self._KEYWORDS_()
        with self._group():
            with self._choice():
                with self._option():
                    self._pattern('[A-Za-z\\p{Ll}\\p{Lu}\\p{Lo}]\\p{M}*')
                    self.name_last_node('value')
                with self._option():
                    self._token('`')
                    self._pattern('[^`]*')
                    self.name_last_node('id')
                    self._token('`')
                self._error('no available options')
        self.ast._define(
            ['id', 'value'],
            []
        )"""
            choice_list = [f"""
                        with self._option():
                            self._pattern('{item}')""".format(item)[1:] for item in id_list]
            option_list = [f"""
                                        with self._option():
                                            self._pattern('{item}')""".format(item)[1:] for item in id_list]
            id_rule = """@tatsumasu('IdentifierAlone')
    def _identifier_alone_(self):  # noqa
        with self._choice():
            with self._option():
                with self._group():
                    with self._choice():""" + '\n' + '\n'.join(choice_list) + r"""
                        self._error('no available options')
                self.name_last_node('const')
            with self._option():
                with self._group():
                    with self._choice():
                        with self._option():
                            with self._ifnot():
                                with self._group():
                                    with self._choice():
                                        with self._option():
                                            self._KEYWORDS_()""" + '\n' + '\n'.join(option_list) + r"""
                                        self._error('no available options')
                            self._pattern('[A-Za-z\\p{Ll}\\p{Lu}\\p{Lo}]\\p{M}*')
                            self.name_last_node('value')
                        with self._option():
                            self._token('`')
                            self._pattern('[^`]*')
                            self.name_last_node('id')
                            self._token('`')
                        self._error('no available options')
            self._error('no available options')
        self.ast._define(
            ['const', 'id', 'value'],
            []
        )"""
            cur_content = cur_content.replace(id_original_rule, id_rule)
        # new function rules
        if 'funcs' in extra_dict:
            funcs_list = extra_dict["funcs"]
            choice_list = [f"""
            with self._option():
                self._pattern('{item}')""".format(item)[1:] for item in funcs_list]
            funcs_original_rule = r"""@tatsumasu()
    def _func_id_(self):  # noqa
        self._token('!!!')"""
            funcs_rule = """@tatsumasu()
    def _func_id_(self):  # noqa
        with self._choice():""" + '\n' + '\n'.join(choice_list) + r"""
            self._error('no available options')"""
            cur_content = cur_content.replace(funcs_original_rule, funcs_rule)
        # new packages
        if 'pkg' in extra_dict:
            funcs_list = extra_dict["pkg"]
            if 'e' in funcs_list:
                funcs_list.remove('e')
                constant_original = r"""@tatsumasu()
    def _constant_(self):  # noqa
        with self._choice():
            with self._option():
                self._pi_()
            with self._option():
                self._infinity_()
            self._error(
                'expecting one of: '
                '<infinity> <pi> π ∞'
            )"""
                constant_new = r"""@tatsumasu()
    def _constant_(self):  # noqa
        with self._choice():
            with self._option():
                self._pi_()
            with self._option():
                self._infinity_()
            with self._option():
                self._e_()
            self._error('no available options')"""
                cur_content = cur_content.replace(constant_original, constant_new)
                keywords_original = r"""@tatsumasu()
    def _KEYWORDS_(self):  # noqa
        self._BUILTIN_KEYWORDS_()"""
                keywords_new = r"""@tatsumasu()
    def _KEYWORDS_(self):  # noqa
        with self._choice():
            with self._option():
                self._BUILTIN_KEYWORDS_()
            with self._option():
                self._e_()
            self._error('no available options')"""
                cur_content = cur_content.replace(keywords_original, keywords_new)
            # normal builtin functions
            builtin_original_rule = r"""@tatsumasu()
    def _builtin_operators_(self):  # noqa
        self._predefined_built_operators_()"""
            choice_list = [f"""
            with self._option():
                self._{item}_()""".format(item)[1:] for item in funcs_list]
            funcs_rule = """@tatsumasu()
    def _builtin_operators_(self):  # noqa
        with self._choice():""" + '\n' + '\n'.join(choice_list) + r"""
            with self._option():
                self._predefined_built_operators_()
            self._error('no available options')"""
            cur_content = cur_content.replace(builtin_original_rule, funcs_rule)
        return cur_content

    def generate_new_parser_files(self):
        la_local_parsers = self.grammar_dir.parent / 'la_local_parsers'
        for f in listdir(la_local_parsers):
            if self.init_hash_value in f:
                init_parser = read_from_file(la_local_parsers / f)
                init_parser = init_parser.replace(self.init_hash_value, 'init')
                save_to_file(init_parser, os.path.join(la_local_parsers, 'init_parser.py'))
            # if self.config_hash_value in f:
            #     config_parser = read_from_file(la_local_parsers / f)
            #     config_parser = config_parser.replace(self.config_hash_value, 'config')
            #     save_to_file(config_parser, os.path.join(la_local_parsers, 'config_parser.py'))
            if self.default_hash_value in f:
                def_parser = read_from_file(la_local_parsers / f)
                def_parser = def_parser.replace(self.default_hash_value, 'default')
                # extra elements
                original_class = r"""def __init__(self, /, config: ParserConfig = None, **settings):
        config = ParserConfig.new(
            config,
            owner=self,
            whitespace=re.compile('(?!.*)'),
            nameguard=None,
            comments_re=None,
            eol_comments_re=None,
            ignorecase=False,
            namechars='',
            parseinfo=False,
            keywords=KEYWORDS,
            start='start',
        )
        config = config.replace(**settings)
        super().__init__(config=config)"""
                new_class = r"""def __init__(self, /, config: ParserConfig = None, **settings):
        config = ParserConfig.new(
            config,
            owner=self,
            whitespace=re.compile('(?!.*)'),
            nameguard=None,
            comments_re=None,
            eol_comments_re=None,
            ignorecase=False,
            namechars='',
            parseinfo=False,
            keywords=KEYWORDS,
            start='start',
        )
        config = config.replace(**settings)
        super().__init__(config=config)
        self.new_id_list = []
        self.new_func_list = []
        self.builtin_list = []
        self.conversion_dict = {}
        self.const_e = False"""
                def_parser = def_parser.replace(original_class, new_class)
                # ids
                id_alone_original_rule = r"""class IdentifierAlone(ModelBase):
    value: Any = None"""
                id_alone_cur_rule = r"""class IdentifierAlone(ModelBase):
    value: Any = None
    const: Any = None"""
                def_parser = def_parser.replace(id_alone_original_rule, id_alone_cur_rule)
                #
                id_original_rule = r"""@tatsumasu('IdentifierAlone')
    def _identifier_alone_(self):  # noqa
        with self._choice():
            with self._option():
                with self._ifnot():
                    self._KEYWORDS_()
                with self._group():
                    with self._choice():
                        with self._option():
                            with self._group():
                                self._pattern('[A-Za-z\\p{Ll}\\p{Lu}\\p{Lo}]\\p{M}*')
                            self.name_last_node('value')
                        with self._option():
                            self._token('`')
                            self._pattern('[^`]*')
                            self.name_last_node('id')
                            self._token('`')

                            self._define(
                                ['id'],
                                []
                            )
                        self._error(
                            'expecting one of: '
                            "'`' [A-Za-z\\p{Ll}\\p{Lu}\\p{Lo}]\\p{M}*"
                        )

                self._define(
                    ['id', 'value'],
                    []
                )
            with self._option():
                with self._group():
                    self._PREFIX_KEYWORD_()
                    with self._group():
                        self._pattern('[A-Za-z\\p{Ll}\\p{Lu}\\p{Lo}]\\p{M}*')
                self.name_last_node('value')
            self._error(
                'expecting one of: '
                "# ' <AND> <ARGMAX> <ARGMIN> <AS>"
                '<BUILTIN_KEYWORDS> <DELTA> <DERIVATIVE>'
                '<EDGES> <EDGESET> <EXP> <FACES>'
                '<FACESET> <FOR> <FROM> <GIVEN> <IF> <IN>'
                '<INDEX> <INITIAL> <INT> <KEYWORDS> <LN>'
                '<LOG> <MATRIX> <MAX> <MESH> <MIN>'
                '<NABLA> <NOT_PREFIX_KEYWORD> <OR>'
                '<OTHERWISE> <PI> <POINTCLOUD> <POLYGON>'
                '<POLYHEDRON> <POUND> <PREFIX_KEYWORD>'
                '<PRIME> <SCALAR> <SEQUENCE>'
                '<SIMPLICIALSET> <SOLVE> <SPARSE> <SQRT>'
                '<SUBJECT_TO> <SUBSET> <TETRAHEDRON>'
                '<TETS> <TETSET> <TRIANGLE> <TUPLE>'
                '<VECTOR> <VERTEXSET> <VERTICES> <WHERE>'
                '<WITH> Mesh SOLVE Solve [Ee]dge[Ss]et'
                '[Ff]ace[Ss]et [Pp]oint [Cc]loud'
                '[Pp]oint[Cc]loud [Pp]olygon[Mm]esh'
                '[Pp]olyhedral[Mm]esh [Ss]implicial[Ss]et'
                '[Tt]et[Ss]et [Tt]etrahedral[Mm]esh'
                '[Tt]riangle[Mm]esh [Vv]ertex[Ss]et [Δ]'
                'and argmax argmin as edges exp faces for'
                'from given if index initial int ln log'
                'matrix max mesh min or otherwise s.t.'
                'scalar sequence solve sparse sqrt'
                'subject to sum tets tuple vector'
                'vertices where with π ℝ ℤ ∇ ∈ ⊂ 𝕕'
            )"""
                id_rule = r"""@tatsumasu('IdentifierAlone')
    def _identifier_alone_(self):  # noqa
        if len(self.new_id_list) > 0:
            with self._choice():
                with self._option():
                    with self._group():
                        with self._choice():
                            for new_id in self.new_id_list:
                                with self._option():
                                    self._pattern(new_id)
                            self._error('no available options')
                    self.name_last_node('const')
                with self._option():
                    with self._ifnot():
                        with self._group():
                            with self._choice():
                                with self._option():
                                    self._KEYWORDS_()
                                for new_id in self.new_id_list:
                                    with self._option():
                                        self._pattern(new_id)
                                self._error('no available options')
                    with self._group():
                        with self._choice():
                            with self._option():
                                with self._group():
                                    self._pattern('[A-Za-z\\p{Ll}\\p{Lu}\\p{Lo}]\\p{M}*')
                                self.name_last_node('value')
                            with self._option():
                                self._token('`')
                                self._pattern('[^`]*')
                                self.name_last_node('id')
                                self._token('`')

                                self._define(
                                    ['id'],
                                    []
                                )
                            self._error(
                                'expecting one of: '
                                "'`' [A-Za-z\\p{Ll}\\p{Lu}\\p{Lo}]\\p{M}*"
                            )

                    self._define(
                        ['id', 'value'],
                        []
                    )
                with self._option():
                    with self._group():
                        with self._choice():
                            with self._option():
                                self._PREFIX_KEYWORD_()
                            for new_id in self.new_id_list:
                                with self._option():
                                    self._pattern(new_id)
                            self._error('no available options')
                        with self._group():
                            self._pattern('[A-Za-z\\p{Ll}\\p{Lu}\\p{Lo}]\\p{M}*')
                    self.name_last_node('value')
                self._error(
                    'expecting one of: '
                    "# ' <AND> <ARGMAX> <ARGMIN> <AS>"
                    '<BUILTIN_KEYWORDS> <DELTA> <DERIVATIVE>'
                    '<EDGES> <EDGESET> <EXP> <FACES>'
                    '<FACESET> <FOR> <FROM> <GIVEN> <IF> <IN>'
                    '<INDEX> <INITIAL> <INT> <KEYWORDS> <LN>'
                    '<LOG> <MATRIX> <MAX> <MESH> <MIN>'
                    '<NABLA> <NOT_PREFIX_KEYWORD> <OR>'
                    '<OTHERWISE> <PI> <POINTCLOUD> <POLYGON>'
                    '<POLYHEDRON> <POUND> <PREFIX_KEYWORD>'
                    '<PRIME> <SCALAR> <SEQUENCE>'
                    '<SIMPLICIALSET> <SOLVE> <SPARSE> <SQRT>'
                    '<SUBJECT_TO> <SUBSET> <TETRAHEDRON>'
                    '<TETS> <TETSET> <TRIANGLE> <TUPLE>'
                    '<VECTOR> <VERTEXSET> <VERTICES> <WHERE>'
                    '<WITH> Mesh SOLVE Solve [Ee]dge[Ss]et'
                    '[Ff]ace[Ss]et [Pp]oint [Cc]loud'
                    '[Pp]oint[Cc]loud [Pp]olygon[Mm]esh'
                    '[Pp]olyhedral[Mm]esh [Ss]implicial[Ss]et'
                    '[Tt]et[Ss]et [Tt]etrahedral[Mm]esh'
                    '[Tt]riangle[Mm]esh [Vv]ertex[Ss]et [Δ]'
                    'and argmax argmin as edges exp faces for'
                    'from given if index initial int ln log'
                    'matrix max mesh min or otherwise s.t.'
                    'scalar sequence solve sparse sqrt'
                    'subject to sum tets tuple vector'
                    'vertices where with π ℝ ℤ ∇ ∈ ⊂ 𝕕'
                )
            self._define(
                ['const', 'id', 'value'],
                []
            )
        else:
            # default
            with self._choice():
                with self._option():
                    with self._ifnot():
                        self._KEYWORDS_()
                    with self._group():
                        with self._choice():
                            with self._option():
                                with self._group():
                                    self._pattern('[A-Za-z\\p{Ll}\\p{Lu}\\p{Lo}]\\p{M}*')
                                self.name_last_node('value')
                            with self._option():
                                self._token('`')
                                self._pattern('[^`]*')
                                self.name_last_node('id')
                                self._token('`')

                                self._define(
                                    ['id'],
                                    []
                                )
                            self._error(
                                'expecting one of: '
                                "'`' [A-Za-z\\p{Ll}\\p{Lu}\\p{Lo}]\\p{M}*"
                            )

                    self._define(
                        ['id', 'value'],
                        []
                    )
                with self._option():
                    with self._group():
                        self._PREFIX_KEYWORD_()
                        with self._group():
                            self._pattern('[A-Za-z\\p{Ll}\\p{Lu}\\p{Lo}]\\p{M}*')
                    self.name_last_node('value')
                self._error(
                    'expecting one of: '
                    "# ' <AND> <ARGMAX> <ARGMIN> <AS>"
                    '<BUILTIN_KEYWORDS> <DELTA> <DERIVATIVE>'
                    '<EDGES> <EDGESET> <EXP> <FACES>'
                    '<FACESET> <FOR> <FROM> <GIVEN> <IF> <IN>'
                    '<INDEX> <INITIAL> <INT> <KEYWORDS> <LN>'
                    '<LOG> <MATRIX> <MAX> <MESH> <MIN>'
                    '<NABLA> <NOT_PREFIX_KEYWORD> <OR>'
                    '<OTHERWISE> <PI> <POINTCLOUD> <POLYGON>'
                    '<POLYHEDRON> <POUND> <PREFIX_KEYWORD>'
                    '<PRIME> <SCALAR> <SEQUENCE>'
                    '<SIMPLICIALSET> <SOLVE> <SPARSE> <SQRT>'
                    '<SUBJECT_TO> <SUBSET> <TETRAHEDRON>'
                    '<TETS> <TETSET> <TRIANGLE> <TUPLE>'
                    '<VECTOR> <VERTEXSET> <VERTICES> <WHERE>'
                    '<WITH> Mesh SOLVE Solve [Ee]dge[Ss]et'
                    '[Ff]ace[Ss]et [Pp]oint [Cc]loud'
                    '[Pp]oint[Cc]loud [Pp]olygon[Mm]esh'
                    '[Pp]olyhedral[Mm]esh [Ss]implicial[Ss]et'
                    '[Tt]et[Ss]et [Tt]etrahedral[Mm]esh'
                    '[Tt]riangle[Mm]esh [Vv]ertex[Ss]et [Δ]'
                    'and argmax argmin as edges exp faces for'
                    'from given if index initial int ln log'
                    'matrix max mesh min or otherwise s.t.'
                    'scalar sequence solve sparse sqrt'
                    'subject to sum tets tuple vector'
                    'vertices where with π ℝ ℤ ∇ ∈ ⊂ 𝕕'
                )"""
                def_parser = def_parser.replace(id_original_rule, id_rule)
                #
                funcs_original_rule = r"""@tatsumasu()
    def _func_id_(self):  # noqa
        self._token('!!!')"""
                funcs_rule = """@tatsumasu()
    def _func_id_(self):  # noqa
        if len(self.new_func_list) > 0:
            with self._choice():
                for new_id in self.new_func_list:
                    with self._option():
                        self._pattern(new_id)
                self._error('no available options')
        else:
            # default
            self._token('!!!')"""
                def_parser = def_parser.replace(funcs_original_rule, funcs_rule)
                # normal builtin functions
                builtin_original_rule = r"""@tatsumasu()
    def _builtin_operators_(self):  # noqa
        self._predefined_built_operators_()"""
                funcs_rule = """@tatsumasu()
    def _builtin_operators_(self):  # noqa
        if len(self.builtin_list) > 0:
            with self._choice():
                for new_builtin in self.builtin_list:
                    with self._option():
                        func = getattr(self, "_{}_".format(new_builtin), None)
                        func()
                with self._option():
                    self._predefined_built_operators_()
                self._error('no available options')
        else:
            self._predefined_built_operators_()"""
                def_parser = def_parser.replace(builtin_original_rule, funcs_rule)
                #
                constant_original = r"""@tatsumasu()
    def _constant_(self):  # noqa
        with self._choice():
            with self._option():
                self._pi_()
            with self._option():
                self._infinity_()
            self._error(
                'expecting one of: '
                '<infinity> <pi> π ∞'
            )"""
                constant_new = r"""@tatsumasu()
    def _constant_(self):  # noqa
        if self.const_e:
            with self._choice():
                with self._option():
                    self._pi_()
                with self._option():
                    self._infinity_()
                with self._option():
                    self._e_()
                self._error('no available options')
        else:
            with self._choice():
                with self._option():
                    self._pi_()
                with self._option():
                    self._infinity_()
                self._error(
                    'expecting one of: '
                    '<infinity> <pi> π ∞'
                )"""
                def_parser = def_parser.replace(constant_original, constant_new)
                keywords_original = r"""@tatsumasu()
    def _KEYWORDS_(self):  # noqa
        self._BUILTIN_KEYWORDS_()"""
                keywords_new = r"""@tatsumasu()
    def _KEYWORDS_(self):  # noqa
        if self.const_e:
            with self._choice():
                with self._option():
                    self._BUILTIN_KEYWORDS_()
                with self._option():
                    self._e_()
                self._error('no available options')
        else:
            self._BUILTIN_KEYWORDS_()"""
                def_parser = def_parser.replace(keywords_original, keywords_new)
                #
                builtin_keys = r"""
            with self._option():
                self._pattern('ℝ')
            with self._option():
                self._pattern('ℤ')
            with self._option():
                self._pattern('ᵀ')"""
                builtin_keys_new = r"""
            with self._option():
                self._pattern('ℝ')
            with self._option():
                self._pattern('ℤ')
            with self._option():
                self._pattern('ᵀ')
            for new_id in self.new_func_list:
                with self._option():
                    self._pattern(new_id)"""
                # def_parser = def_parser.replace(builtin_keys, builtin_keys_new)
                for builtin_func_list in PACKAGES_FUNC_DICT.values():
                    for builtin_func in builtin_func_list:
                        builtin_func_name_key = r"""@tatsumasu()
    def _{}_(self):  # noqa
        self._pattern('{}')""".format(builtin_func.upper(), builtin_func)
                        builtin_func_name_key_new = r"""@tatsumasu()
    def _{}_(self):  # noqa
        if '{}' in self.conversion_dict:
            self._pattern(self.conversion_dict['{}'])
        else:
            self._pattern('{}')""".format(builtin_func.upper(), builtin_func, builtin_func, builtin_func)
                        def_parser = def_parser.replace(builtin_func_name_key, builtin_func_name_key_new)
                #
                save_to_file(def_parser, os.path.join(la_local_parsers, 'default_parser.py'))


def recreate_local_parser_cache():
    """
    The new parser will work as long as the grammar modification doesn't include the following rules:
    KEYWORDS, constant, builtin_operators, func_id, identifier_alone
    """
    ### WARNING: This will delete and re-create the cache and 'la_local_parsers' directories.
    import iheartla.la_parser.parser
    PM = iheartla.la_parser.parser._parser_manager

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
    iheartla.la_parser.parser.create_parser()

    print('## Re-creating config parser.')
    # PM.create_config_parser()

    print('## Waiting for them to be saved.')
    for thread in PM.parser_file_manager.save_threads: thread.join()

    print('## Copying the cache dir contents into the local dir.')
    for f in Path(PM.cache_dir).glob('*.py'):
        shutil.copy( f, la_local_parsers )

    print('## Modifying default parsers')
    PM.parser_file_manager.generate_new_parser_files()

    print('## Done.')
