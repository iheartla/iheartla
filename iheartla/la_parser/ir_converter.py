from .ir_visitor import *
from ..la_inference import inference as Infer

class IRConverter(IRVisitor):
    def __init__(self, parse_type=None):
        super().__init__(parse_type=parse_type)

    def convert_la_type(self, la_type):
        inf_type = None
        if la_type.is_matrix():
            if la_type.is_integer_element():
                inf_type = Infer.TypeMfixed(rows=la_type.rows, cols=la_type.cols)
            else:
                inf_type = Infer.TypeMfixedDouble(rows=la_type.rows, cols=la_type.cols)
        elif la_type.is_vector():
            if la_type.is_integer_element():
                inf_type = Infer.TypeVfixed(rows=la_type.rows)
            else:
                inf_type = Infer.TypeVfixedDouble(rows=la_type.rows)
        return inf_type

    def convert_inf_type(self, inf_type):
        la_type = None
        if isinstance(inf_type, Infer.TypeM):
            la_type = MatrixType(rows=inf_type.rows, cols=inf_type.cols)
            if isinstance(inf_type, Infer.TypeMfixed) or isinstance(inf_type, Infer.TypeMrow) or isinstance(inf_type, Infer.TypeMcol):
                la_type.is_int = True
        elif isinstance(inf_type, Infer.TypeV):
            la_type = VectorType(rows=inf_type.rows)
            if isinstance(inf_type, Infer.TypeVfixed):
                la_type.is_int = True
        return la_type

    def visit_code(self, node, **kwargs):
        self.content = ''
        # Create type environment
        env_dict = {}
        for param in self.parameters:
            env_dict[param] = self.convert_la_type(self.symtable[param])
        for sym in self.undef_symbols:
            env_dict[sym] = Infer.TypeVariable()
        print("env_dict: {}".format(env_dict))
        # Type inference
        hm_ast = self.visit(node)
        print("hm_ast: {}".format(hm_ast))
        ty_list, mgu_list, t_list = Infer.infer_exp(env_dict, hm_ast)
        info = ''
        valid_cnt = 0
        for cur_index in range(len(ty_list)):
            ty = ty_list[cur_index]
            mgu = mgu_list[cur_index]
            t = t_list[cur_index]
            print("ty:{}, mgu:{}, t:{}".format(ty, mgu, t))
            # Convert inferred types to LaTypes, add back as parameters
            multi_tips = ''
            skip = False
            for sym in self.undef_symbols:
                v_ty = Infer.apply(mgu, env_dict[sym])
                if not Infer.check_final_mtype(v_ty):
                    skip = True
                    continue
                v_type = self.convert_inf_type(v_ty)
                if isinstance(v_ty, Infer.TypeM):
                    multi_tips += "{} is {}, rows:{}, cols:{}; ".format(sym, v_ty, v_ty.rows, v_ty.cols)
                elif isinstance(v_ty, Infer.TypeV):
                    multi_tips += "{} is {}, rows:{}; ".format(sym, v_ty, v_ty.rows)
                else:
                    multi_tips += "{} is {}; ".format(sym, v_ty)
                if cur_index == 0:
                    self.symtable[sym] = v_type
                    self.parameters.append(sym)
            if skip:
                continue
            valid_cnt += 1
            info += multi_tips + '\n'
            if cur_index == 0:
                self.symtable[self.ret_symbol] = self.convert_inf_type(ty)
        info = 'There are {} options:\n'.format(valid_cnt) + info + '\n'
        if len(ty_list) > 1:
            assert False, info
            print(info)
        return ''


    def visit_block(self, node, **kwargs):
        pre_node = None
        for index in range(len(node.stmts)):
            if node.stmts[len(node.stmts)-1-index].node_type == IRNodeType.Assignment:
                stat_info = self.visit(node.stmts[index], **kwargs)
                stat_info.body = pre_node
            else:
                stat_info = self.visit(node.stmts[index], **kwargs)
            pre_node = stat_info
        return pre_node

    def visit_assignment(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        return Infer.Let(node.left.get_main_id(), right_info, None)

    def visit_add(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        return Infer.Multi_Apply(Infer.Identifier("add"), [left_info, right_info])

    def visit_mul(self, node, **kwargs):
        left_info = self.visit(node.left, **kwargs)
        right_info = self.visit(node.right, **kwargs)
        return Infer.Multi_Apply(Infer.Identifier("mul"), [left_info, right_info])

    def visit_id(self, node, **kwargs):
        return Infer.Identifier(node.get_name())
