from .ir_printer import *
from ..la_geometry.geometry_helper import get_gp_func_impl
from ..la_tools.module_manager import CacheModuleManager
import copy


class CodeFrame(object):
    def __init__(self, parse_type=None, desc='', include='', struct='', rand_data='', main='', namespace=''):
        self.parse_type = parse_type
        self.desc = desc            # comment for iheartla file
        self.include = include      # headers
        self.namespace = namespace  # using namespace
        self.struct = struct        # return structure
        self.rand_data = rand_data  # random data
        self.main = main            # main function
        self.expr = ''              # expression content in tex
        self.expr_dict = {}         # raw content : MathML code
        self.pre_str = ''
        self.post_str = ''
        self.pre_block = ''
        self.extra_include = ''     # gp modules
        self.extra_funcs = []       # builtin gp functions

    def get_code(self):
        content = ''
        if self.parse_type == ParserTypeEnum.EIGEN:
            content = self.desc + self.include + self.extra_include + self.namespace + self.get_extra_func_impl() + self.struct + '\n\n' + self.rand_data + '\n\n\n' + self.main
        elif self.parse_type == ParserTypeEnum.NUMPY:
            content = self.desc + self.include + self.extra_include + self.namespace + self.get_extra_func_impl() + self.struct + '\n\n' + self.rand_data + '\n\n\n' + self.main
        elif self.parse_type == ParserTypeEnum.MATLAB:
            content = self.extra_include + self.namespace + self.get_extra_func_impl() + self.struct  # struct already contains everything
        elif self.parse_type == ParserTypeEnum.LATEX:
            content = self.main
        elif self.parse_type == ParserTypeEnum.MATHJAX:
            content = self.main
        elif self.parse_type == ParserTypeEnum.MACROMATHJAX:
            content = self.main
        elif self.parse_type == ParserTypeEnum.MATHML:
            content = self.main
        return content

    def get_extra_func_impl(self):
        return ''.join([get_gp_func_impl(func, la_type=self.parse_type) for func in self.extra_funcs])


    def get_mathjax_content(self):
        return self.pre_str + self.expr + self.post_str

    def reset(self):
        self.desc = ''
        self.include = ''
        self.struct = ''
        self.main = ''
        self.rand_data = ''
        self.expr = ''
        self.pre_str = ''
        self.post_str = ''
        self.expr_dict.clear()
        self.extra_include = ''
        self.extra_funcs.clear()


class CodeModule(object):
    def __init__(self, frame=None, name=CLASS_NAME, syms=None, r_syms=None, params=None, func_sig_dict=None):
        self.frame = frame   # code frame
        self.name = name     # module name
        self.syms = syms     # imported symbols
        self.r_syms = r_syms   # imported symbols (renamed)
        self.params = params # parameters
        self.func_sig_dict = func_sig_dict # function signature -> identity local function name


class CodeGen(IRPrinter):
    def __init__(self, parse_type=None):
        super().__init__(parse_type=parse_type)
        self.code_frame = CodeFrame(parse_type)

    def init_type(self, type_walker, func_name):
        self.code_frame.reset()
        super().init_type(type_walker, func_name)

    def visit_code(self, node, **kwargs):
        self.module_list = node.module_list
        self.module_syms = node.module_syms
        self.content = self.pre_str + self.visit(node) + self.post_str
        return copy.deepcopy(self.code_frame)

    def visit_start(self, node, **kwargs):
        return self.visit(node.stat, **kwargs)

    def visit_add(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.content = left_info.content + ' + ' + right_info.content
        left_info.pre_list += right_info.pre_list
        return left_info

    def visit_sub(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        left_info.content = left_info.content + ' - ' + right_info.content
        left_info.pre_list += right_info.pre_list
        return left_info

    def visit_sub_expr(self, node, **kwargs):
        value_info = self.visit(node.value, **kwargs)
        value_info.content = '(' + value_info.content + ')'
        return value_info

    def visit_expression(self, node, **kwargs):
        exp_info = self.visit(node.value, **kwargs)
        if node.sign:
            exp_info.content = '-' + exp_info.content
        return exp_info

    def visit_function(self, node, **kwargs):
        name_info = self.visit(node.name, **kwargs)
        pre_list = []
        params = []
        if node.params:
            for param in node.params:
                param_info = self.visit(param, **kwargs)
                params.append(param_info.content)
                pre_list += param_info.pre_list
        content = "{}({})".format(name_info.content, ', '.join(params))
        return CodeNodeInfo(content, pre_list)

    def visit_matrix_rows(self, node, **kwargs):
        ret = []
        pre_list = []
        if node.rs:
            rs_info = self.visit(node.rs, **kwargs)
            ret = ret + rs_info.content
            pre_list += rs_info.pre_list
        if node.r:
            r_info = self.visit(node.r, **kwargs)
            ret.append(r_info.content)
            pre_list += r_info.pre_list
        return CodeNodeInfo(ret, pre_list)

    def visit_matrix_row(self, node, **kwargs):
        ret = []
        pre_list = []
        if node.rc:
            rc_info = self.visit(node.rc, **kwargs)
            ret += rc_info.content
            pre_list += rc_info.pre_list
        if node.exp:
            exp_info = self.visit(node.exp, **kwargs)
            ret.append(exp_info.content)
            pre_list += exp_info.pre_list
        return CodeNodeInfo(ret, pre_list)

    def visit_matrix_row_commas(self, node, **kwargs):
        ret = []
        pre_list = []
        if node.value:
            value_info = self.visit(node.value, **kwargs)
            ret += value_info.content
            pre_list += value_info.pre_list
        if node.exp:
            exp_info = self.visit(node.exp, **kwargs)
            ret.append(exp_info.content)
            pre_list += exp_info.pre_list
        return CodeNodeInfo(ret, pre_list)

    def visit_exp_in_matrix(self, node, **kwargs):
        exp_info = self.visit(node.value, **kwargs)
        if node.sign:
            exp_info.content = '-' + exp_info.content
        return exp_info

    def get_func_prefix(self):
        return ''
    def get_builtin_func_name(self, name):
        res = name
        for key, module_data in self.builtin_module_dict.items():
            if key in CLASS_PACKAGES:
                if key == MESH_HELPER:
                    if name in module_data.inverse_dict:
                        res = module_data.inverse_dict[name]
        return res

    def convert_overloaded_name(self, name):
        # mapp builtin func names to the different backends
        cur_dict = BACKEND_OVERLOADING_DICT[self.parse_type]
        if name in cur_dict:
            return cur_dict[name]
        return name
    
    def get_mesh_str(self, mesh):
        # prepend self. if necessary
        return mesh

    def visit_gp_func(self, node, **kwargs):
        if node.func_name not in self.code_frame.extra_funcs:
            self.code_frame.extra_funcs.append(node.func_name)
        params_content_list = []
        pre_list = []
        for param in node.params:
            param_info = self.visit(param, **kwargs)
            pre_list += param_info.pre_list
            params_content_list.append(param_info.content)
        content = node.identity_name
        content = self.convert_overloaded_name(content)
        # content = "{}.{}({})".format(self.get_func_prefix(), self.get_builtin_func_name(content), ', '.join(params_content_list))
        if node.params[0].la_type.is_mesh():
            # if the first param is a mesh
            content = "{}.{}({})".format(self.get_mesh_str(params_content_list[0]), self.get_builtin_func_name(content), ', '.join(params_content_list[1:]))
        else:
            if node.func_type == GPType.NonZeros:
                content = "{}({})".format(self.get_builtin_func_name(content), ', '.join(params_content_list))
            elif node.func_type == GPType.IndicatorVector:
                indicator_dim_dict = {
                    VERTICES_TO_VECTOR: 'n_vertices()',
                    EDGES_TO_VECTOR: 'n_edges()',
                    FACES_TO_VECTOR: 'n_faces()',
                    TETS_TO_VECTOR: 'n_tets()'
                }
                content = "indicator({}, {}.{})".format(', '.join(params_content_list), self.get_mesh_str(node.params[0].la_type.owner), indicator_dim_dict[self.get_builtin_func_name(content)])
            else:
                # mesh is still necessary
                content = "{}.{}({})".format(self.get_mesh_str(node.params[0].la_type.owner), self.get_builtin_func_name(content), ', '.join(params_content_list))
        return CodeNodeInfo(content, pre_list=pre_list)