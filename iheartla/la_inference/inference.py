#!/usr/bin/env python
"""
.. module:: inference
   :synopsis: An implementation of the Hindley Milner type checking algorithm
              based on the code by Robert Smallshire.
"""

from __future__ import print_function
from enum import IntEnum
from enum import Enum, IntEnum, IntFlag
import copy
from .inference_logger import log_content, log_perm
import math


class ConsType(IntEnum):
    ConsInvalid = -1
    ConsEq = 0
    ConsIn = 1
    ConsLess = 2
    ConsLessM = 3


add_fun_list = []
mul_fun_list = []


class TypeConstraint(object):
    def __init__(self, lhs=None, rhs=None, ctype=ConsType.ConsInvalid, mid=None):
        self.lhs = lhs
        self.rhs = rhs
        self.mid = mid
        self.ctype = ctype
        if ctype == ConsType.ConsLess and mid is not None:
            self.ctype = ConsType.ConsLessM

    def __str__(self):
        return "type:{}, lhs:{}, rhs:{}, mid:{}".format(self.ctype, self.lhs, self.rhs, self.mid)

    def get_active_vars(self):
        if self.ctype == ConsType.ConsLessM:
            return union_set(free_type_variable(self.lhs),
                             intersect(free_type_variable(self.mid), free_type_variable(self.rhs)))
        return union_set(free_type_variable(self.lhs), free_type_variable(self.rhs))

    def satisfied(self, remain_cons):
        u = intersect(difference(free_type_variable(self.rhs), self.mid), get_active_vars(remain_cons))
        # log_content("ftv:{}, next_con.mid:{}, get_active_vars(remain_cons):{}".format(free_type_variable(self.rhs), self.mid, get_active_vars(remain_cons)))
        if u is None or len(u) == 0:
            return True
        return False


# =======================================================#
# Class definitions for the abstract syntax tree nodes
class AstTreeNode(object):
    def __init__(self):
        self.m_set = set()  # monomorphic set

    def add_m(self, tyv):
        self.m_set.add(tyv)


class Lambda(AstTreeNode):
    """Lambda abstraction"""

    def __init__(self, v, body):
        super().__init__()
        self.v = v
        self.body = body

    def __str__(self):
        return "(fn {v} => {body})".format(v=self.v, body=self.body)

    def add_m(self, tyv):
        super(Lambda, self).add_m(tyv)
        self.body.add_m(tyv)


class Identifier(AstTreeNode):
    """Identifier"""

    def __init__(self, name):
        super().__init__()
        self.name = name

    def __str__(self):
        return self.name


class Apply(AstTreeNode):
    """Function application"""

    def __init__(self, fn, arg):
        super().__init__()
        self.fn = fn
        self.arg = arg

    def __str__(self):
        return "({fn} {arg})".format(fn=self.fn, arg=self.arg)

    def add_m(self, tyv):
        super(Apply, self).add_m(tyv)
        self.fn.add_m(tyv)
        self.arg.add_m(tyv)


class Let(AstTreeNode):
    """Let binding"""

    def __init__(self, v, defn, body):
        super().__init__()
        self.v = v
        self.defn = defn
        self.body = body

    def __str__(self):
        return "(let {v} = {defn} in {body})".format(v=self.v, defn=self.defn, body=self.body)

    def add_m(self, tyv):
        super(Let, self).add_m(tyv)
        self.defn.add_m(tyv)
        self.body.add_m(tyv)


class Letrec(AstTreeNode):
    """Letrec binding"""

    def __init__(self, v, defn, body):
        super().__init__()
        self.v = v
        self.defn = defn
        self.body = body

    def __str__(self):
        return "(letrec {v} = {defn} in {body})".format(v=self.v, defn=self.defn, body=self.body)

    def add_m(self, tyv):
        super(Letrec, self).add_m(tyv)
        self.defn.add_m(tyv)
        self.body.add_m(tyv)


# =======================================================#
# Exception types
class InferenceError(Exception):
    """Raised if the type inference algorithm cannot infer types successfully"""

    def __init__(self, message):
        self.__message = message

    message = property(lambda self: self.__message)

    def __str__(self):
        return str(self.message)


class ParseError(Exception):
    """Raised if the type environment supplied for is incomplete"""

    def __init__(self, message):
        self.__message = message

    message = property(lambda self: self.__message)

    def __str__(self):
        return str(self.message)


class TypeCon(object):
    def __init__(self, name=None):
        super().__init__()
        self.name = name


class TypeM(TypeCon):
    def __init__(self, name=None, rows=None, cols=None):
        super().__init__(name)
        self.rows = rows
        self.cols = cols

    def __repr__(self):
        return "TypeM"


class TypeMDouble(TypeM):
    # def __init__(self, name=None, rows=None, cols=None):
    #     super().__init__(name=name, rows=rows, cols=cols)

    def __repr__(self):
        return "TypeMDouble"


class TypeMrow(TypeM):
    def __repr__(self):
        return "TypeMrow"


class TypeMrowDouble(TypeM):
    def __repr__(self):
        return "TypeMrowDouble"


class TypeMcol(TypeM):
    def __repr__(self):
        return "TypeMcol"


class TypeMcolDouble(TypeM):
    def __repr__(self):
        return "TypeMcolDouble"


class TypeMfixed(TypeM):
    def __repr__(self):
        return "TypeMfixed"


class TypeMfixedDouble(TypeM):
    def __repr__(self):
        return "TypeMfixedDouble"


inherited_dict = {
    "TypeMDouble": ["TypeM", "TypeMDouble", "TypeMrow", "TypeMrowDouble", "TypeMcol", "TypeMcolDouble", "TypeMfixed",
                    "TypeMfixedDouble"],
    "TypeM": ["TypeM", "TypeMrow", "TypeMcol", "TypeMfixed"],
    "TypeMrowDouble": ["TypeMrow", "TypeMrowDouble", "TypeMfixed", "TypeMfixedDouble"],
    "TypeMrow": ["TypeMrow", "TypeMfixed"],
    "TypeMcolDouble": ["TypeMcol", "TypeMcolDouble", "TypeMfixed", "TypeMfixedDouble"],
    "TypeMcol": ["TypeMcol", "TypeMfixed"],
    "TypeMfixedDouble": ["TypeMfixed", "TypeMfixedDouble"],
    "TypeMfixed": ["TypeMfixed"],
    "double": ["double", "int"],
}


# =======================================================#
# Types and type constructors
class TypeVariable(object):
    """A type variable standing for an arbitrary type.
    All type variables have a unique id, but names are only assigned lazily,
    when required.
    """
    next_variable_id = 0

    def __init__(self):
        self.id = TypeVariable.next_variable_id
        TypeVariable.next_variable_id += 1
        self.instance = None
        self.__name = None

    next_variable_name = 'a'

    @property
    def name(self):
        """Names are allocated to TypeVariables lazily, so that only TypeVariables
        present after analysis consume names.
        """
        if self.__name is None:
            self.__name = '_' + TypeVariable.next_variable_name
            TypeVariable.next_variable_name = chr(ord(TypeVariable.next_variable_name) + 1)
        return self.__name

    def __str__(self):
        if self.instance is not None:
            return str(self.instance)
        else:
            return self.name

    def __repr__(self):
        return "TypeVariable(id = {0}, name={1})".format(self.id, self.name)


class TypeScheme(object):
    def __init__(self, name, quantified_types=[], type_op=None, env=None):
        self.name = name
        self.quantified_types = quantified_types
        self.type_op = type_op
        self.env = env

    def instantiate(self):
        new_types = copy.deepcopy(self.type_op.types)
        if len(self.quantified_types) > 0:
            ty_dict = {}
            for ty in self.quantified_types:
                new_type = TypeVariable()
                ty_dict[ty.id] = new_type
                log_content("Instantiate TypeScheme, scheme:({}), {} -> {}".format(str(self), ty, new_type))
            for index in range(len(new_types)):
                if isinstance(new_types[index], TypeOperator):
                    new_types[index].instantiate(ty_dict)
                else:
                    if new_types[index].id in ty_dict:
                        new_types[index] = ty_dict[new_types[index].id]
        return TypeOperator(self.name, new_types)

    def get_ftvs(self):
        ftvs = self.type_op.get_ftvs()
        return difference(ftvs, set(self.quantified_types))

    def empty_quantified(self):
        return len(self.quantified_types) == 0

    def __str__(self):
        quantified_dsp = [str(tp) for tp in self.quantified_types]
        return "name:{}, quantified:{}, type:{}".format(self.name, ' '.join(quantified_dsp), str(self.type_op))

    def __repr__(self):
        return self.__str__()


class TypeOperator(object):
    """An n-ary type constructor which builds a new type from old"""

    def __init__(self, name, types):
        self.name = name
        self.types = types

    def __str__(self):
        num_types = len(self.types)
        if num_types == 0:
            return self.name
        elif num_types == 2:
            return "({0} {1} {2})".format(str(self.types[0]), self.name, str(self.types[1]))
        else:
            return "{0} {1}".format(self.name, ' '.join(self.types))

    def __repr__(self):
        return self.__str__()

    def generalize(self, env):
        new_env = env.copy()
        tyv_set = set()
        ftvs = self.get_ftvs()
        for ty in ftvs:
            if ty.name not in new_env:
                tyv_set.add(ty)
        log_content("Generalize ftvs: {}".format(ftvs))
        log_content("Generalize tyv_set: {}".format(tyv_set))
        type_scheme = TypeScheme(self.name, list(tyv_set), self, new_env)
        log_content("Generalize result: {}".format(str(type_scheme)))
        # log_content(str(type_scheme))
        return type_scheme

    def instantiate(self, ty_dict):
        if len(self.types) > 0:
            def modify_types():
                for cur_index in range(len(self.types)):
                    if isinstance(self.types[cur_index], TypeOperator):
                        self.types[cur_index].instantiate(ty_dict)
                    else:
                        if self.types[cur_index].id in ty_dict:
                            self.types[cur_index] = ty_dict[self.types[cur_index].id]

            if isinstance(self.types, list):
                modify_types()
            elif isinstance(self.types, tuple):
                self.types = list(self.types)
                modify_types()
                self.types = tuple(self.types)

    def get_ftvs(self):
        ftv_dict = {}
        for ty in self.types:
            if isinstance(ty, TypeVariable):
                ftv_dict[ty.name] = ty
                # ftvs.add(ty)
            elif isinstance(ty, TypeOperator):
                # type operator
                new_dict = gen_env_dict(ty.get_ftvs())
                ftv_dict.update(new_dict)
                # ftvs = ftvs.union()
        ftvs = set(ftv_dict.values())
        return ftvs


class Function(TypeOperator):
    """A binary type constructor which builds function types"""

    def __init__(self, from_type, to_type, name="->"):
        super(Function, self).__init__(name, [from_type, to_type])


def Multi_Function(types):
    if len(types) == 2:
        return Function(types[0], types[1])
    else:
        return Function(types[0], Multi_Function(types[1:]))


def Multi_Apply(ident, args):
    if len(args) == 1:
        return Apply(ident, args[0])
    else:
        return Apply(Multi_Apply(ident, args[:-1]), args[-1])


def free_type_variable(x):
    if isinstance(x, TypeScheme):
        return x.get_ftvs()
    elif isinstance(x, TypeOperator):
        return x.get_ftvs()
    elif isinstance(x, set) or isinstance(x, list):
        ftvs = set()
        for e in x:
            ftvs.union(free_type_variable(e))
        return ftvs
    return set()


def instantiate(x):
    if isinstance(x, TypeScheme):
        return x.instantiate()
    else:
        return x


def get_active_vars(cons):
    atvs = set()
    for c in cons:
        atvs = union_set(atvs, c.get_active_vars())
    return atvs


# Basic types are constructed with a nullary type constructor
Integer = TypeOperator("int", [])  # Basic integer
Double = TypeOperator("double", [])  # Basic double
Bool = TypeOperator("bool", [])  # Basic bool
# Matrix = TypeOperator("matrix", [])
# Vector = TypeOperator("vector", [])
Matrix = TypeM()
MatrixDouble = TypeMDouble()
MatrixRow = TypeMrow()
MatrixRowDouble = TypeMrowDouble()
MatrixCol = TypeMcol()
MatrixColDouble = TypeMcolDouble()
MatrixFixed = TypeMfixed()
MatrixFixedDouble = TypeMfixedDouble()

# =======================================================#
# Type inference machinery
constraint = []


def merge_assum(lhs, rhs):
    # log_content("merge_assum, lhs:{}, rhs:{}".format(lhs, rhs))
    same_keys = set(lhs.keys()).intersection(rhs.keys())
    same_dict = {}
    if len(same_keys) > 0:
        def get_list(value):
            if isinstance(value, list):
                return value
            else:
                return [value]

        for k in same_keys:
            same_dict[k] = get_list(lhs[k]) + get_list(rhs[k])
    lhs.update(rhs)
    lhs.update(same_dict)
    # log_content("merge_assum, result:{}".format(lhs))
    return lhs


def analyse(node, env=None):
    """Computes the type of the expression given by node.

    The type of the node is computed in the context of the
    supplied type environment env. Data types can be introduced into the
    language simply by having a predefined set of identifiers in the initial
    environment. environment; this way there is no need to change the syntax or, more
    importantly, the type-checking program when extending the language.

    Args:
        node: The root of the abstract syntax tree.
        env: The type environment is a mapping of expression identifier names
            to type assignments.
            to type assignments.
        non_generic: A set of non-generic variables, or None

    Returns:
        The computed type of the expression.

    Raises:
        InferenceError: The type of the expression could not be inferred, for example
            if it is not possible to unify two types such as Integer and Bool
        ParseError: The abstract syntax tree rooted at node could not be parsed
    """
    assum = {}  # assumptions
    cons = set()  # constraints
    if isinstance(node, TypeCon):
        return node, assum, cons
    elif isinstance(node, Identifier):
        if node.name in env:
            v_type = instantiate(env[node.name])
            log_content("Node Identifier, existed {}:{}".format(node.name, str(v_type)))
            # v_type = env[node.name]
        elif is_integer_literal(node.name):
            v_type = Integer
        elif is_double_literal(node.name):
            v_type = Double
        else:
            v_type = TypeVariable()
            assum[node.name] = v_type
            log_content("Node Identifier, Name {}:{}".format(node.name, v_type))
        return v_type, assum, cons
    elif isinstance(node, Apply):
        fun_type, assum, cons1 = analyse(node.fn, env)
        arg_type, assum2, cons2 = analyse(node.arg, env)
        result_type = TypeVariable()
        # log_content("Node Apply, fun_type:{}, result name: {}".format(fun_type.name, result_type))
        cons = cons1.union(cons2)
        assum = merge_assum(assum, assum2)  # update assum
        var_fun = Function(arg_type, result_type)
        if isinstance(node.fn, Identifier):
            if node.fn.name == 'add':
                global add_fun_list
                add_fun_list.append(var_fun)
            elif node.fn.name == 'mul':
                global mul_fun_list
                mul_fun_list.append(var_fun)
        if isinstance(fun_type, list):
            cons.add(TypeConstraint(var_fun, fun_type, ConsType.ConsIn))
        else:
            cons.add(TypeConstraint(var_fun, fun_type, ConsType.ConsEq))
        return result_type, assum, cons
    elif isinstance(node, Lambda):
        arg_type = TypeVariable()
        node.body.add_m(arg_type)
        result_type, assum, cons = analyse(node.body, env)
        if node.v in assum:
            # parameter may not be used inside function
            x_type = assum[node.v]
            del assum[node.v]
            if isinstance(x_type, list):
                for x_tp in x_type:
                    cons.add(TypeConstraint(x_tp, arg_type, ConsType.ConsEq))
            else:
                cons.add(TypeConstraint(x_type, arg_type, ConsType.ConsEq))
        log_content("Node Lambda, arg name {}:{}".format(node.v, arg_type))
        return Function(arg_type, result_type), assum, cons
    elif isinstance(node, Let):
        defn_type, assum, cons1 = analyse(node.defn, env)
        if node.body is not None:
            body_type, assum2, cons2 = analyse(node.body, env)
            x_type = assum2[node.v]
            cons = cons1.union(cons2)
            assum = merge_assum(assum, assum2)  # update assum
            del assum[node.v]
            if isinstance(x_type, list):
                for x_tp in x_type:
                    cons.add(TypeConstraint(x_tp, defn_type, ConsType.ConsLess, node.m_set))
            else:
                cons.add(TypeConstraint(x_type, defn_type, ConsType.ConsLess, node.m_set))
            return body_type, assum, cons
        else:
            return defn_type, assum, cons1
    elif isinstance(node, Letrec):
        defn_type, assum, cons1 = analyse(node.defn, env)
        body_type, assum2, cons2 = analyse(node.body, env)
        x_type = assum2[node.v]
        cons = cons1.union(cons2)
        assum = merge_assum(assum, assum2)  # update assum
        del assum[node.v]
        if isinstance(x_type, list):
            for x_tp in x_type:
                cons.add(TypeConstraint(x_tp, defn_type, ConsType.ConsLess, node.m_set))
        else:
            cons.add(TypeConstraint(x_type, defn_type, ConsType.ConsLess, node.m_set))
        return body_type, assum, cons
    assert 0, "Unhandled syntax node {0}".format(type(node))


### == Constraint Solver ==
def empty():
    return {}


def const_type(x):
    if isinstance(x, TypeCon):
        return True
    if isinstance(x, TypeOperator) and len(x.types) == 0:
        return True
    return False


def apply(s, t):
    if const_type(t) or isinstance(t, Identifier):
        return t
    elif isinstance(t, TypeOperator):
        def get_list():
            new_dict = {}
            res = []
            for ty in t.types:
                res.append(apply(s, ty))
            return res

        if isinstance(t.types, list):
            return TypeOperator(t.name, get_list())
        else:
            return TypeOperator(t.name, tuple(get_list()))
    elif isinstance(t, TypeScheme):
        new_op = apply(s, t.type_op)
        new_set = apply(s, set(t.env.values()))
        # # todo: apply to typescheme
        # q_types = []
        # for tp in t.quantified_types:
        #     q_types.append(apply(s, tp))
        # tp_scheme = TypeScheme(t.name, q_types, apply(s, t.type_op))
        tp_scheme = generalize(gen_env_dict(new_set), new_op)
        log_content("Apply t: {}".format(str(t)))
        log_content("Apply s: {}".format(str(s)))
        log_content("Apply tp_scheme: {}".format(str(tp_scheme)))
        return tp_scheme
    elif isinstance(t, TypeVariable):
        return s.get(t.name, t)
    elif isinstance(t, set):
        new_set = set()
        for item in t:
            new_set.add(apply(s, item))
        return new_set
    else:
        return t


def applyList(s, xs):
    """ Apply substitution on a list of constraints
    :param s: substitution
    :param xs: list of constraints
    :return: new list
    """
    res_list = []
    for cons in xs:
        if cons.ctype == ConsType.ConsLess or cons.ctype == ConsType.ConsEq:
            res_list.append(TypeConstraint(apply(s, cons.lhs), apply(s, cons.rhs), cons.ctype))
        elif cons.ctype == ConsType.ConsIn:
            res_list.append(TypeConstraint(apply(s, cons.lhs), cons.rhs, cons.ctype))
        else:
            res_list.append(TypeConstraint(apply(s, cons.lhs), apply(s, cons.rhs), cons.ctype, apply(s, cons.mid)))
    # for res in xs:
    #     log_content("pre res:{}".format(res))
    # for res in res_list:
    #     log_content("res:{}".format(res))
    return res_list if isinstance(xs, list) else set(res_list)


def unify(x, y):
    if isinstance(x, Apply) and isinstance(y, Apply):
        s1 = unify(x.fn, y.fn)
        s2 = unify(apply(s1, x.arg), apply(s1, y.arg))
        return compose(s2, s1)
    elif const_type(x) and const_type(y):
        if isinstance(x, Identifier) and isinstance(y, Identifier) and x.name == y.name:
            return empty()
        elif type(x).__name__ == type(y).__name__:
            # log_content("x:{}, y:{}".format(x, y))
            return empty()
        else:
            raise InferenceError("Type mismatch: {} and {}".format(x, y))
    elif isinstance(x, TypeOperator) and isinstance(y, TypeOperator):
        if len(x.types) != len(y.types):
            raise InferenceError("Wrong number of arguments")
        s1 = unify(x.types[0], y.types[0])
        s2 = unify(apply(s1, x.types[1]), apply(s1, y.types[1]))
        # log_content("s2: {}".format(str(s2)))
        return compose(s2, s1)
    elif isinstance(x, TypeVariable):
        return bind(x.name, y)
    elif isinstance(y, TypeVariable):
        return bind(y.name, x)
    else:
        raise InferenceError('\n'.join([
            "Type mismatch: ",
            "Given: ", "\t" + str(x),
            "Expected: ", "\t" + str(y)
        ]))


def unify_matrix(x, y):
    if isinstance(x, TypeMfixed):
        pass
    elif isinstance(x, TypeMfixed):
        pass


def split_cons(cons):
    if len(cons) <= 1:
        next_con = list(cons)[0]
        if next_con.ctype == ConsType.ConsIn:
            find, mgu, new_list = find_proto(next_con.lhs, next_con.rhs)
            if find:
                # next_con.rhs = new_list
                if len(new_list) != 1:
                    # decrease the original options
                    next_con.rhs = new_list
                    log_content("split_cons, trimed con: {}".format(next_con))
                    find_generic_cos(next_con)
            else:
                print("not find:{}".format(next_con))
                raise InferenceError("not find: ")
        return next_con, set()
    else:
        next_le_cons = None
        next_m_cons = None

        def get_remain_cons(cur_con, cur_cons):
            res = []
            for tmp in cur_cons:
                if tmp != cur_con:
                    res.append(tmp)
            return res

        # Always solve first type
        for con in cons:
            if con.ctype == ConsType.ConsEq:
                cons.remove(con)
                return con, cons
        # Other cons handled together
        in_cnt = 0
        in_con = None
        for con in cons:
            if con.ctype == ConsType.ConsIn:
                find, mgu, new_list = find_proto(con.lhs, con.rhs)
                if find:
                    if len(new_list) == 1:
                        # There may be multiple options, solve the single list first
                        cons.remove(con)
                        return con, cons
                    else:
                        # decrease the original options
                        con.rhs = new_list
                        log_content("split_cons, trimed con: {}".format(con))
                        in_cnt += 1
                        in_con = con
            elif con.ctype == ConsType.ConsLess:
                next_le_cons = con if next_le_cons is None else next_le_cons
            elif con.ctype == ConsType.ConsLessM:
                next_m_cons = con if next_m_cons is None and con.satisfied(get_remain_cons(con, cons)) else next_m_cons
            else:
                pass
        next_con = next_m_cons if next_m_cons is not None else next_le_cons
        if next_con is None:
            # todo: Handle multiple options
            log_content("Error or tips, multiple options for overloaded operators")
            if in_cnt == 1:
                print("in_cnt: {}".format(in_cnt))
                # find_generic_cos(in_con)
                next_con = in_con
                ##################
                find, mgu, new_list = find_proto(next_con.lhs, next_con.rhs)
                if find:
                    # next_con.rhs = new_list
                    if len(new_list) != 1:
                        # decrease the original options
                        next_con.rhs = new_list
                        log_content("split_cons, trimed con: {}".format(next_con))
                        find_generic_cos(next_con)
                print("trimmmmmmmmm")
            else:
                next_con, cons = split_minimum_ty(cons)
                return next_con, cons
        cons.remove(next_con)
        return next_con, cons


def split_minimum_ty(cons):
    """
    Find the constraint with the minimum type variables
    :param cons:
    :return:
    """
    next_con = None
    cur_cnt = math.inf
    for cur_con in cons:
        if cur_con.ctype == ConsType.ConsIn:
            tmp_cnt = get_ty_cnts(cur_con.lhs)
            if tmp_cnt < cur_cnt:
                cur_cnt = tmp_cnt
                next_con = cur_con
    cons.remove(next_con)
    ############
    find, mgu, new_list = find_proto(next_con.lhs, next_con.rhs)
    if find:
        if len(new_list) != 1:
            # decrease the original options
            next_con.rhs = new_list
            log_content("split_cons, trimed con: {}".format(next_con))
            find_generic_cos(next_con)
    return next_con, cons


def get_ty_cnts(tpo):
    """
    Get the number of TypeVariables
    :param tpo: TypeOperator, TypeVariable or TypeCons
    :return:
    """
    cnt = 0
    if isinstance(tpo, TypeOperator):
        for ty in tpo.types:
            cnt += get_ty_cnts(ty)
    elif isinstance(tpo, TypeVariable):
        cnt = 1
    return cnt


def generalize(env, x):
    if isinstance(x, TypeOperator):
        return x.generalize(env)
    else:
        return x


def gen_env_dict(m_set):
    res = {}
    for m in m_set:
        res[m.name] = m
    return res


def find_proto(source, target_list):
    """
    :param source: function with type variables
    :param target_list: overloaded functions
    :return:
    """
    find = False
    mgu = empty()
    new_list = []
    for target in target_list:
        try:
            mgu = unify(source, target)
            # log_content("find_proto, cur mgu: {}".format(mgu))
            if len(mgu) > 0:
                find = True
                new_list.append(target)
        except InferenceError:
            pass
            # log_content("cur mgu: error")
    log_content("find_proto, cur new_list: {}".format(new_list))
    return find, mgu, new_list


def find_generic_cos(cons):
    return
    """
    Reduce the number of cons
    :param cons:
    :return:
    """
    # cur_cons = cons.rhs[0]
    # for cur_index in range(1, len(cons.rhs)):
    #     if not is_more_generic_opt(cur_cons, cons.rhs[cur_index]):
    #         cur_cons = cons.rhs[cur_index]
    # print("find_generic_cos, cur_cons: {}".format(cur_cons))
    # cons.rhs = cur_cons
    # cons.ctype = ConsType.ConsEq
    #
    old_list = cons.rhs
    new_list = []
    for cur_index in range(len(old_list)):
        if len(new_list) == 0:
            new_list.append(old_list[cur_index])
        else:
            handled = False
            for inner_index in range(len(new_list)):
                if is_similar_types(old_list[cur_index], new_list[inner_index]):
                    handled = True
                    if is_more_generic_opt(old_list[cur_index], new_list[inner_index]):
                        new_list[inner_index] = old_list[cur_index]
                    break
            if not handled:
                new_list.append(old_list[cur_index])
    print("find_generic_cos, old_list: {}".format(old_list))
    print("find_generic_cos, new_list: {}".format(new_list))
    cons.rhs = new_list
    if len(new_list) > 1:
        print("more than one!!!!!!")
        # cons.rhs = new_list[0]
        cons.ctype = ConsType.ConsIn
    else:
        cons.rhs = new_list[0]
        cons.ctype = ConsType.ConsEq


def is_similar_types(lhs, rhs):
    if isinstance(lhs, TypeOperator) and isinstance(rhs, TypeOperator):
        similar = True
        if len(lhs.types) != len(rhs.types):
            similar = False
        else:
            for cur_index in range(len(lhs.types)):
                if not is_similar_types(lhs.types[cur_index], rhs.types[cur_index]):
                    similar = False
                    break
    elif isinstance(lhs, TypeVariable) and isinstance(rhs, TypeVariable):
        similar = True
    elif isinstance(lhs, TypeCon) and isinstance(rhs, TypeCon):
        similar = True
    else:
        similar = False
    return similar


def is_more_generic(lhs, rhs):
    if isinstance(lhs, TypeOperator) and isinstance(rhs, TypeOperator):
        return is_more_generic_opt(lhs, rhs)
    else:
        return is_more_generic_tp(lhs, rhs)


def is_more_generic_opt(lhs_opt, rhs_opt):
    more_generic = True
    for cur_index in range(len(lhs_opt.types)):
        if not is_more_generic(lhs_opt.types[cur_index], rhs_opt.types[cur_index]):
            more_generic = False
            break
    return more_generic


def is_more_generic_tp(lhs_tp, rhs_tp):
    more_generic = False
    if isinstance(lhs_tp, TypeM) and isinstance(rhs_tp, TypeM):
        if rhs_tp.__class__.__name__ in inherited_dict[lhs_tp.__class__.__name__]:
            more_generic = True
    return more_generic


def solve_cons(cons, cur_mgu_list=[]):
    # log_content("solve_cons cons:{}".format(cons))
    # for con in cons:
    #     log_content(con)
    solution_list = []
    solution_mgu_list = []
    if len(cons) == 0:
        s = dict()
        solution_list.append(s)
        solution_mgu_list.append(cur_mgu_list)
    else:
        next_con, remain_cons = split_cons(cons)
        # log_content("next_con: {}".format(next_con))
        if next_con.ctype == ConsType.ConsEq:
            mgu = unify(next_con.lhs, next_con.rhs)
            log_content("size:{}, cur mgu: {{".format(len(remain_cons)))
            log_dict(mgu)
            log_content("}")
            cur_mgu_list.append(mgu)
            tmp_sol_list, tmp_sol_mgu_list = solve_cons(applyList(mgu, remain_cons), cur_mgu_list)
            for sol_index in range(len(tmp_sol_list)):
                solution_list.append(compose(tmp_sol_list[sol_index], mgu))
                solution_mgu_list.append(tmp_sol_mgu_list[sol_index])
            # s = compose(, mgu)
        elif next_con.ctype == ConsType.ConsLessM:
            if next_con.satisfied(remain_cons):
                type_scheme = generalize(gen_env_dict(next_con.mid), next_con.rhs)
                if type_scheme.empty_quantified():
                    new_cons = TypeConstraint(next_con.lhs, type_scheme.type_op, ConsType.ConsEq)
                else:
                    new_cons = TypeConstraint(next_con.lhs, type_scheme, ConsType.ConsLess)
                log_content("New cons: {}".format(str(new_cons)))
                remain_cons.add(new_cons)
                log_cons(remain_cons)  # log
                solution_list, solution_mgu_list = solve_cons(remain_cons, cur_mgu_list)
            else:
                assert False, "Need to check"
        elif next_con.ctype == ConsType.ConsLess:
            new_cons = TypeConstraint(next_con.lhs, instantiate(next_con.rhs), ConsType.ConsEq)
            log_content("New cons: {}".format(str(new_cons)))
            remain_cons.add(new_cons)
            log_cons(remain_cons)  # log
            solution_list, solution_mgu_list = solve_cons(remain_cons, cur_mgu_list)
        elif next_con.ctype == ConsType.ConsIn:
            # Multiple options
            find, mgu, new_list = find_proto(next_con.lhs, next_con.rhs)
            if find:
                new_cons_list = split_in_cons(next_con)
                for new_next_con in new_cons_list:
                    try:
                        new_remain_set = copy.deepcopy(remain_cons)
                        new_remain_set.add(new_next_con)
                        tmp_solution_list, tmp_solution_mgu_list = solve_cons(new_remain_set,
                                                                              copy.deepcopy(cur_mgu_list))
                        solution_list += tmp_solution_list
                        solution_mgu_list += tmp_solution_mgu_list
                    except InferenceError:
                        print("This branch doesn't work")
                    except Exception as e:
                        print("This branch doesn't work")
            else:
                print("un find!!!!!")
            # log_content("New new : {}".format(str(next_con)))
            # find, mgu, new_list = find_proto(next_con.lhs, next_con.rhs)
            # if find:
            #     log_content("size:{}, cur mgu: {{".format(len(remain_cons)))
            #     log_dict(mgu)
            #     log_content("}")
            #     cur_mgu_list.append(mgu)
            #     s = compose(solve_cons(applyList(mgu, remain_cons), cur_mgu_list), mgu)
    # log_content("current substitution: {}".format(s))
    return solution_list, solution_mgu_list


def split_in_cons(cons):
    """
    Split constraint with type ConsType.ConsIn into several constraints with type ConsType.ConsEq
    :param cons:
    :return:
    """
    new_list = []
    for cur_index in range(len(cons.rhs)):
        new_list.append(TypeConstraint(cons.lhs, cons.rhs[cur_index], ConsType.ConsEq))
    return new_list


def difference(lhs, rhs):
    lhs_dict = gen_env_dict(lhs)
    rhs_dict = gen_env_dict(rhs)
    res = set()
    for k in set(lhs_dict) - set(rhs_dict):
        res.add(lhs_dict[k])
    return res


def intersect(lhs, rhs):
    lhs_dict = gen_env_dict(lhs)
    rhs_dict = gen_env_dict(rhs)
    res = set()
    for k in set(lhs_dict).intersection(set(rhs_dict)):
        res.add(lhs_dict[k])
    return res


def union_set(lhs, rhs):
    lhs_dict = gen_env_dict(lhs)
    rhs_dict = gen_env_dict(rhs)
    res = set()
    for k in set(lhs_dict).union(set(rhs_dict)):
        if k in set(lhs_dict):
            res.add(lhs_dict[k])
        else:
            res.add(rhs_dict[k])
    return res


def bind(n, x):
    if x == n:
        return empty()
    elif occurs_check(n, x):
        raise InferenceError("recursive unification: {} and {}".format(n, x))
    else:
        return dict([(n, x)])


def occurs_check(n, x):
    # ftvs =
    # log_content("occurs_check: {}, {}, {}".format(str(n), x, ftvs))
    # if len(ftvs) > 0:
    #     for ftv in ftvs:
    #         log_content("ftv:{}, n:{}".format(ftv.name, n))
    #         if ftv.name == n:
    #             return True
    # return False
    return any(n == t.name for t in free_type_variable(x))


def union(s1, s2):
    nenv = s1.copy()
    nenv.update(s2)
    return nenv


def compose(s1, s2):
    s3 = dict((t, apply(s1, u)) for t, u in s2.items())
    # log_content("s1:{}, s2:{}, s3:{}".format(s1, s2, union(s1, s3)))
    return union(s1, s3)


def is_integer_literal(name):
    result = True
    try:
        int(name)
    except ValueError:
        result = False
    return result


def is_double_literal(name):
    result = True
    try:
        float(name)
    except ValueError:
        result = False
    return result


def log_dict(dict):
    for e in dict:
        log_content("{}: {}".format(e, dict[e]))


def log_cons(cons):
    log_content("Current cons: {}".format(len(cons)))
    for con in cons:
        log_content(con)


# ==================================================================#
# Example code to exercise the above
def infer_exp(env, node):
    infer_ty_list = []
    new_gmu_list = []
    t_list = []

    env.update(TOP_ENV)
    log_perm("node info: {}".format(str(node)))
    log_content("Top env:")
    log_dict(env)
    log_content("")
    global constraint
    constraint = []
    global add_fun_list
    add_fun_list.clear()
    global mul_fun_list
    mul_fun_list.clear()
    try:
        t, assum, cons = analyse(node, env)
        log_content("\nFinal assumption: {}".format(assum))
        log_content("\nInitial cons: {}".format(len(cons)))
        for item in assum:
            if item not in env:
                raise InferenceError("Undefined variables exist: {}".format(item))
            cons.add(TypeConstraint(assum[item], env[item], ConsType.ConsEq))
        log_content("\nCurrent cons: {}".format(len(cons)))
        for con in cons:
            log_content(con)
        cur_mgu_list = []

        sol_list, sol_mgu_list = solve_cons(cons, cur_mgu_list)
        # mgu = solve_cons(cons, cur_mgu_list)
        for total_index in range(len(sol_list)):
            print("total_index:{}".format(total_index))
            mgu = sol_list[total_index]
            cur_mgu_list = sol_mgu_list[total_index]
            try:
                # iterate each option
                log_content("mgu: {")
                log_dict(mgu)
                log_content("}")
                infer_ty = apply(mgu, t)
                log_content("Inferred type str: {}".format(str(t)))
                log_perm("Inferred value: {}".format(infer_ty))
                #####################################################3
                new_gmu = gen_new_mgu_list(cur_mgu_list)
                # infer_ty = new_gmu[t.name]
                infer_ty = apply(new_gmu, t)
                # check dimensions
                assert_list = []
                unresolved = True
                cnt = 0
                while unresolved:
                    unresolved = False
                    cnt += 1
                    log_content("cnt: {}".format(cnt))
                    # Handle addition
                    unresolved_add = handle_addition(new_gmu)
                    if unresolved_add:
                        unresolved = True
                    # Handle multiplication
                    unresolved_mul = handle_multiplication(new_gmu)
                    if unresolved_mul:
                        unresolved = True
                    # log_content("ty:{}, ty.rows:{}, cols:{}, addr:{}".format(infer_ty, infer_ty.rows, infer_ty.cols, id(infer_ty)))
                    if cnt > 5:
                        unresolved = False
                    if cnt < 5:
                        unresolved = False
                infer_ty_list.append(infer_ty)
                new_gmu_list.append(new_gmu)
                t_list.append(t)
            except Exception as e:
                pass
        # return infer_ty, new_gmu, t
        return infer_ty_list, new_gmu_list, t_list
    except (ParseError, InferenceError) as e:
        log_content(e)


def get_param(cur_mgu, var_type):
    if isinstance(var_type, TypeVariable):
        var_param = cur_mgu[var_type.name]
    else:
        var_param = var_type
    return var_param


def resolved_matrix(m_value):
    is_resolved = True
    if isinstance(m_value, TypeMrowDouble) or isinstance(m_value, TypeMrow):
        is_resolved = m_value.rows is not None
    elif isinstance(m_value, TypeMcolDouble) or isinstance(m_value, TypeMcol):
        is_resolved = m_value.cols is not None
    elif isinstance(m_value, TypeMfixedDouble) or isinstance(m_value, TypeMfixed):
        is_resolved = m_value.cols is not None and m_value.rows is not None
    return is_resolved


def gen_new_mgu_list(mgu_list):
    log_content("add_fun_list: {}".format(add_fun_list))
    log_content("mul_fun_list: {}".format(mul_fun_list))
    # Re-process the mgu, create new instances and find the dependency
    log_content("Before mul, mgu_list:{}".format(mgu_list))
    new_gmu = {}
    for cur_index in range(len(mgu_list)):
        cur_mgu = mgu_list[len(mgu_list) - 1 - cur_index]
        for key, value in cur_mgu.items():
            if isinstance(value, TypeM):
                # if value.rows is not None or value.cols is not None:
                #     new_gmu[key] = value
                # else:
                #     new_gmu[key] = copy.deepcopy(value)
                new_gmu[key] = copy.deepcopy(value)
                log_content("key:{}, cur_index:{}, value:{}, addr:{}".format(key, cur_index, new_gmu[key],
                                                                             id(new_gmu[key])))
            elif isinstance(value, TypeOperator):
                new_tpo = copy.deepcopy(value)
                for type_index in range(len(new_tpo.types)):
                    if isinstance(new_tpo.types[type_index], TypeVariable):
                        new_tpo.types[type_index] = new_gmu[new_tpo.types[type_index].name]
                        log_content("key:{}, cur_index:{}, type_index:{}, value:{}, addr:{}".format(key, cur_index,
                                                                                                    type_index,
                                                                                                    new_tpo.types[
                                                                                                        type_index], id(
                                new_tpo.types[type_index])))
                new_gmu[key] = new_tpo
    log_content("new_gmu:{}".format(new_gmu))
    return new_gmu


def handle_addition(new_gmu):
    unresolved = False
    for var_fun in add_fun_list:
        first_param = get_param(new_gmu, var_fun.types[0])
        if isinstance(first_param, TypeM):
            # matrix addition
            remain_func = get_param(new_gmu, var_fun.types[1])
            sec_param = get_param(new_gmu, remain_func.types[0])
            ret_param = get_param(new_gmu, remain_func.types[1])
            assert isinstance(sec_param, TypeM)
            # rows
            if first_param.rows is not None:
                if sec_param.rows is not None:
                    assert first_param.rows == sec_param.rows
                    # assert_list.append(first_param.rows, sec_param.rows)
                else:
                    sec_param.rows = first_param.rows
                ret_param.rows = first_param.rows
            else:
                if sec_param.rows is not None:
                    if ret_param.rows is None:
                        ret_param.rows = sec_param.rows
                    else:
                        assert ret_param.rows == sec_param.rows
                    first_param.rows = sec_param.rows
                else:
                    if ret_param.rows is not None:
                        # Fill back
                        first_param.rows = ret_param.rows
                        sec_param.rows = ret_param.rows
            # cols
            if first_param.cols is not None:
                if sec_param.cols is not None:
                    assert first_param.cols == sec_param.cols
                    # assert_list.append(first_param.cols, sec_param.cols)
                else:
                    sec_param.cols = first_param.cols
                ret_param.cols = first_param.cols
            else:
                if sec_param.cols is not None:
                    if ret_param.cols is None:
                        ret_param.cols = sec_param.cols
                    else:
                        assert ret_param.cols == sec_param.cols
                    first_param.cols = sec_param.cols
                else:
                    if ret_param.cols is not None:
                        # Fill back
                        first_param.cols = ret_param.cols
                        sec_param.cols = ret_param.cols
            resolved = resolved_matrix(ret_param)
            if not (resolved and resolved_matrix(first_param) and resolved_matrix(sec_param)):
                unresolved = True
            log_content("add_index:\n"
                        "fir param:{}, rows:{}, cols:{}, addr:{};\n"
                        "sec param:{}, rows:{}, cols:{}, addr:{};\n"
                        "ret param:{}, rows:{}, cols:{}, addr:{};\n".format(
                first_param, first_param.rows, first_param.cols, id(first_param),
                sec_param, sec_param.rows, sec_param.cols, id(sec_param),
                ret_param, ret_param.rows, ret_param.cols, id(ret_param)))
    return unresolved


def handle_multiplication(new_gmu):
    unresolved = False
    for mul_index in range(len(mul_fun_list)):
        var_fun = mul_fun_list[mul_index]
        first_param = get_param(new_gmu, var_fun.types[0])
        remain_func = get_param(new_gmu, var_fun.types[1])
        sec_param = get_param(new_gmu, remain_func.types[0])
        ret_param = get_param(new_gmu, remain_func.types[1])
        if isinstance(first_param, TypeM):
            # matrix addition
            if isinstance(sec_param, TypeM):
                # Matrix * Matrix
                # rows
                if first_param.cols is not None:
                    if sec_param.rows is not None:
                        assert first_param.cols == sec_param.rows
                    else:
                        sec_param.rows = first_param.cols
                else:
                    if sec_param.rows is not None:
                        first_param.cols = sec_param.rows
                if ret_param.rows is None:
                    ret_param.rows = first_param.rows
                else:
                    if first_param.rows is None:
                        # Fill back
                        first_param.rows = ret_param.rows
                    else:
                        assert ret_param.rows == first_param.rows
                if ret_param.cols is None:
                    ret_param.cols = sec_param.cols
                else:
                    if sec_param.cols is None:
                        # Fill back
                        sec_param.cols = ret_param.cols
                    else:
                        assert ret_param.cols == first_param.cols
                log_content("mul_index:{};\n"
                            "fir param:{}, rows:{}, cols:{}, addr:{};\n"
                            "sec param:{}, rows:{}, cols:{}, addr:{};\n"
                            "ret param:{}, rows:{}, cols:{}, addr:{};\n".format(mul_index,
                                                                                first_param, first_param.rows,
                                                                                first_param.cols, id(first_param),
                                                                                sec_param, sec_param.rows,
                                                                                sec_param.cols, id(sec_param),
                                                                                ret_param, ret_param.rows,
                                                                                ret_param.cols, id(ret_param)))
            else:
                # Matrix * Scalar
                if ret_param.rows is None:
                    ret_param.rows = first_param.rows
                else:
                    if first_param.rows is None:
                        # Fill back
                        first_param.rows = ret_param.rows
                    else:
                        assert first_param.rows == ret_param.rows
                if ret_param.cols is None:
                    ret_param.cols = first_param.cols
                else:
                    if first_param.cols is None:
                        # Fill back
                        first_param.cols = ret_param.cols
                    else:
                        assert first_param.cols == ret_param.cols
        else:
            if isinstance(sec_param, TypeM):
                # Scalar * Matrix
                if ret_param.rows is None:
                    ret_param.rows = sec_param.rows
                else:
                    if sec_param.rows is None:
                        # Fill back
                        sec_param.rows = ret_param.rows
                    else:
                        assert sec_param.rows == ret_param.rows
                if ret_param.cols is None:
                    ret_param.cols = sec_param.cols
                else:
                    if sec_param.cols is None:
                        # Fill back
                        sec_param.cols = ret_param.cols
                    else:
                        assert sec_param.cols == ret_param.cols
            else:
                # Scalar * Scalar
                pass
        resolved = resolved_matrix(ret_param)
        if not (resolved and resolved_matrix(first_param) and resolved_matrix(sec_param)):
            unresolved = True
    return unresolved


def check_final_mtype(m_value):
    """
    Check whether the matrix type is precise
    :param m_value: any type
    :return:
    """
    is_match = True
    if isinstance(m_value, TypeMrowDouble) or isinstance(m_value, TypeMrow):
        is_match = m_value.rows is not None and m_value.cols is None
    elif isinstance(m_value, TypeMcolDouble) or isinstance(m_value, TypeMcol):
        is_match = m_value.cols is not None and m_value.rows is None
    elif isinstance(m_value, TypeMfixedDouble) or isinstance(m_value, TypeMfixed):
        is_match = m_value.cols is not None and m_value.rows is not None
    return is_match


TOP_ENV = {
    "mul": [  #
        Function(MatrixCol, Function(MatrixRow, Matrix)),
        Function(MatrixCol, Function(MatrixRowDouble, MatrixDouble)),
        Function(MatrixCol, Function(MatrixFixed, MatrixCol)),
        Function(MatrixCol, Function(MatrixFixedDouble, MatrixColDouble)),
        #
        Function(MatrixColDouble, Function(MatrixRow, MatrixDouble)),
        Function(MatrixColDouble, Function(MatrixRowDouble, MatrixDouble)),
        Function(MatrixColDouble, Function(MatrixFixed, MatrixColDouble)),
        Function(MatrixColDouble, Function(MatrixFixedDouble, MatrixColDouble)),
        #
        Function(MatrixFixed, Function(MatrixRow, MatrixRow)),
        Function(MatrixFixed, Function(MatrixRowDouble, MatrixRowDouble)),
        Function(MatrixFixed, Function(MatrixFixed, MatrixFixed)),
        Function(MatrixFixed, Function(MatrixFixedDouble, MatrixFixedDouble)),
        #
        Function(MatrixFixedDouble, Function(MatrixRow, MatrixRowDouble)),
        Function(MatrixFixedDouble, Function(MatrixRowDouble, MatrixRowDouble)),
        Function(MatrixFixedDouble, Function(MatrixFixed, MatrixFixedDouble)),
        Function(MatrixFixedDouble, Function(MatrixFixedDouble, MatrixFixedDouble)),
        #
        Function(Integer, Function(Matrix, Matrix)),
        Function(Integer, Function(MatrixDouble, MatrixDouble)),
        Function(Integer, Function(MatrixRow, MatrixRow)),
        Function(Integer, Function(MatrixRowDouble, MatrixRowDouble)),
        Function(Integer, Function(MatrixCol, MatrixCol)),
        Function(Integer, Function(MatrixColDouble, MatrixColDouble)),
        Function(Integer, Function(MatrixFixed, MatrixFixed)),
        Function(Integer, Function(MatrixFixedDouble, MatrixFixedDouble)),
        #
        Function(Matrix, Function(Integer, Matrix)),
        Function(MatrixDouble, Function(Integer, MatrixDouble)),
        Function(MatrixRow, Function(Integer, MatrixRow)),
        Function(MatrixRowDouble, Function(Integer, MatrixRowDouble)),
        Function(MatrixCol, Function(Integer, MatrixCol)),
        Function(MatrixColDouble, Function(Integer, MatrixColDouble)),
        Function(MatrixFixed, Function(Integer, MatrixFixed)),
        Function(MatrixFixedDouble, Function(Integer, MatrixFixedDouble)),
        #
        Function(Double, Function(Matrix, MatrixDouble)),
        Function(Double, Function(MatrixDouble, MatrixDouble)),
        Function(Double, Function(MatrixRow, MatrixRowDouble)),
        Function(Double, Function(MatrixRowDouble, MatrixRowDouble)),
        Function(Double, Function(MatrixCol, MatrixColDouble)),
        Function(Double, Function(MatrixColDouble, MatrixColDouble)),
        Function(Double, Function(MatrixFixed, MatrixFixedDouble)),
        Function(Double, Function(MatrixFixedDouble, MatrixFixedDouble)),

        Function(Matrix, Function(Double, MatrixDouble)),
        Function(MatrixDouble, Function(Double, MatrixDouble)),
        Function(MatrixRow, Function(Double, MatrixRowDouble)),
        Function(MatrixRowDouble, Function(Double, MatrixRowDouble)),
        Function(MatrixCol, Function(Double, MatrixColDouble)),
        Function(MatrixColDouble, Function(Double, MatrixColDouble)),
        Function(MatrixFixed, Function(Double, MatrixFixedDouble)),
        Function(MatrixFixedDouble, Function(Double, MatrixFixedDouble))
    ],
    "add": [Function(Matrix, Function(Matrix, Matrix)),
            Function(Matrix, Function(MatrixDouble, MatrixDouble)),
            Function(Matrix, Function(MatrixRow, MatrixRow)),
            Function(Matrix, Function(MatrixRowDouble, MatrixRowDouble)),
            Function(Matrix, Function(MatrixCol, MatrixCol)),
            Function(Matrix, Function(MatrixColDouble, MatrixColDouble)),
            Function(Matrix, Function(MatrixFixed, MatrixFixed)),
            Function(Matrix, Function(MatrixFixedDouble, MatrixFixedDouble)),
            #
            Function(MatrixDouble, Function(Matrix, MatrixDouble)),
            Function(MatrixDouble, Function(MatrixDouble, MatrixDouble)),
            Function(MatrixDouble, Function(MatrixRow, MatrixRowDouble)),
            Function(MatrixDouble, Function(MatrixRowDouble, MatrixRowDouble)),
            Function(MatrixDouble, Function(MatrixCol, MatrixColDouble)),
            Function(MatrixDouble, Function(MatrixColDouble, MatrixColDouble)),
            Function(MatrixDouble, Function(MatrixFixed, MatrixFixedDouble)),
            Function(MatrixDouble, Function(MatrixFixedDouble, MatrixFixedDouble)),
            #
            Function(MatrixRow, Function(Matrix, MatrixRow)),
            Function(MatrixRow, Function(MatrixDouble, MatrixRowDouble)),
            Function(MatrixRow, Function(MatrixRow, MatrixRow)),
            Function(MatrixRow, Function(MatrixRowDouble, MatrixRowDouble)),
            Function(MatrixRow, Function(MatrixCol, MatrixFixed)),
            Function(MatrixRow, Function(MatrixColDouble, MatrixFixedDouble)),
            Function(MatrixRow, Function(MatrixFixed, MatrixFixed)),
            Function(MatrixRow, Function(MatrixFixedDouble, MatrixFixedDouble)),
            #
            Function(MatrixRowDouble, Function(Matrix, MatrixRowDouble)),
            Function(MatrixRowDouble, Function(MatrixDouble, MatrixRowDouble)),
            Function(MatrixRowDouble, Function(MatrixRow, MatrixRowDouble)),
            Function(MatrixRowDouble, Function(MatrixRowDouble, MatrixRowDouble)),
            Function(MatrixRowDouble, Function(MatrixCol, MatrixRowDouble)),
            Function(MatrixRowDouble, Function(MatrixColDouble, MatrixRowDouble)),
            Function(MatrixRowDouble, Function(MatrixFixed, MatrixRowDouble)),
            Function(MatrixRowDouble, Function(MatrixFixedDouble, MatrixRowDouble)),
            #
            Function(MatrixCol, Function(Matrix, MatrixCol)),
            Function(MatrixCol, Function(MatrixDouble, MatrixColDouble)),
            Function(MatrixCol, Function(MatrixRow, MatrixFixed)),
            Function(MatrixCol, Function(MatrixRowDouble, MatrixFixedDouble)),
            Function(MatrixCol, Function(MatrixCol, MatrixCol)),
            Function(MatrixCol, Function(MatrixColDouble, MatrixColDouble)),
            Function(MatrixCol, Function(MatrixFixed, MatrixFixed)),
            Function(MatrixCol, Function(MatrixFixedDouble, MatrixFixedDouble)),
            #
            Function(MatrixColDouble, Function(Matrix, MatrixColDouble)),
            Function(MatrixColDouble, Function(MatrixDouble, MatrixColDouble)),
            Function(MatrixColDouble, Function(MatrixRow, MatrixFixedDouble)),
            Function(MatrixColDouble, Function(MatrixRowDouble, MatrixFixedDouble)),
            Function(MatrixColDouble, Function(MatrixCol, MatrixColDouble)),
            Function(MatrixColDouble, Function(MatrixColDouble, MatrixColDouble)),
            Function(MatrixColDouble, Function(MatrixFixed, MatrixFixedDouble)),
            Function(MatrixColDouble, Function(MatrixFixedDouble, MatrixFixedDouble)),
            #
            Function(MatrixFixed, Function(Matrix, MatrixFixed)),
            Function(MatrixFixed, Function(MatrixDouble, MatrixFixedDouble)),
            Function(MatrixFixed, Function(MatrixRow, MatrixFixed)),
            Function(MatrixFixed, Function(MatrixRowDouble, MatrixFixedDouble)),
            Function(MatrixFixed, Function(MatrixCol, MatrixFixed)),
            Function(MatrixFixed, Function(MatrixColDouble, MatrixFixedDouble)),
            Function(MatrixFixed, Function(MatrixFixed, MatrixFixed)),
            Function(MatrixFixed, Function(MatrixFixedDouble, MatrixFixedDouble)),
            #
            Function(MatrixFixedDouble, Function(Matrix, MatrixFixedDouble)),
            Function(MatrixFixedDouble, Function(MatrixDouble, MatrixFixedDouble)),
            Function(MatrixFixedDouble, Function(MatrixRow, MatrixFixedDouble)),
            Function(MatrixFixedDouble, Function(MatrixRowDouble, MatrixFixedDouble)),
            Function(MatrixFixedDouble, Function(MatrixCol, MatrixFixedDouble)),
            Function(MatrixFixedDouble, Function(MatrixColDouble, MatrixFixedDouble)),
            Function(MatrixFixedDouble, Function(MatrixFixed, MatrixFixedDouble)),
            Function(MatrixFixedDouble, Function(MatrixFixedDouble, MatrixFixedDouble)),
            #
            Function(Integer, Function(Double, Double)),
            Function(Double, Function(Integer, Double)),
            Function(Double, Function(Double, Double)),
            Function(Integer, Function(Integer, Integer))],
}


def main():
    """The main example program.

    Sets up some predefined types using the type constructors TypeVariable,
    TypeOperator and Function.  Creates a list of example expressions to be
    evaluated. Evaluates the expressions, log_contenting the type or errors arising
    from each.

    Returns:
        None
    """

    var1 = TypeVariable()
    var2 = TypeVariable()
    pair_type = TypeOperator("*", (var1, var2))

    var3 = TypeVariable()
    var4 = TypeVariable()

    my_env = {"pair": generalize({}, Function(var1, Function(var2, pair_type))),
              "true": Bool,
              "f": TypeVariable(),
              "g": TypeVariable(),
              "h": TypeVariable(),
              "cond": Function(Bool, Function(var3, Function(var3, var3))),
              "zero": Function(Integer, Bool),
              "pred": Function(Integer, Integer),
              # "index": [Function(Matrix, Function(Integer, Integer)),
              "index": [Function(MatrixColDouble, Function(Integer, Double))],
              "test_f": generalize({}, Function(var4, var4)),
              "merge": Function(Integer, Function(Bool, Bool)),
              "aa": generalize({}, Function(var2, Function(TypeVariable(), Function(TypeVariable(), TypeVariable())))),
              "times": Function(Integer, Function(Integer, Integer))}
    pair = Apply(Apply(Identifier("pair"),
                       Apply(Identifier("f"),
                             Identifier("4"))),
                 Apply(Identifier("f"),
                       Identifier("true")))

    examples = [
        # factorial
        # Letrec("factorial",  # letrec factorial =
        #        Lambda("n",  # fn n =>
        #               Apply(
        #                   Apply(  # cond (zero n) 1
        #                       Apply(Identifier("cond"),  # cond (zero n)
        #                             Apply(Identifier("zero"), Identifier("n"))),
        #                       Identifier("1")),
        #                   Apply(  # times n
        #                       Apply(Identifier("times"), Identifier("n")),
        #                       Apply(Identifier("factorial"),
        #                             Apply(Identifier("pred"), Identifier("n")))
        #                   )
        #               )
        #               ),  # in
        #        Apply(Identifier("factorial"), Identifier("5"))
        #        ),

        # Should fail:
        # fn x => (pair(x(3) (x(true)))
        # Lambda("x",
        #        Apply(
        #            Apply(Identifier("pair"),
        #                  Apply(Identifier("x"), Identifier("3"))),
        #            Apply(Identifier("x"), Identifier("3")))),
        # Apply(
        #     Apply(Identifier("aa"), Identifier("3")),
        #     Identifier("3")),

        # pair(f(3), f(true))
        # Apply(
        #     Apply(Identifier("pair"), Apply(Identifier("f"), Identifier("4"))),
        #     Apply(Identifier("f"), Identifier("true"))),

        # let f = (fn x => x) in ((pair (f 4)) (f true))
        # Let("f", Lambda("x", Identifier("x")), pair),

        # Apply(Apply(Identifier("pair"), Identifier("3")), Identifier("true")),
        # Let("f", Lambda("x", Identifier("x")),
        #     Apply(Apply(Identifier("merge"), Apply(Identifier("f"), Identifier("3"))), Apply(Identifier("f"), Identifier("true")))),

        # Apply(Identifier("merge"), Apply(Identifier("test_f"), Identifier("3"))),
        # Apply(Apply(Identifier("merge"), Apply(Identifier("test_f"), Identifier("3"))), Apply(Identifier("test_f"), Identifier("true"))),
        # Apply(Identifier("test_f"), Apply(Identifier("test_f"), Identifier("4"))),

        # fn f => f f (fail)
        # Lambda("f", Apply(Identifier("f"), Identifier("f"))),

        # let g = fn f => 5 in g g
        # Let("g",
        #     Lambda("f", Identifier("5")),
        #     Apply(Identifier("g"), Identifier("g"))),

        # example that demonstrates generic and non-generic variables:
        # fn g => let f = fn x => g in pair (f 3, f true)
        # Lambda("g",
        #        Let("f",
        #            Lambda("x", Identifier("g")),
        #            Apply(
        #                Apply(Identifier("pair"),
        #                      Apply(Identifier("f"), Identifier("3"))
        #                      ),
        #                Apply(Identifier("f"), Identifier("true"))))),

        # Let("h",
        #     Lambda("g",
        #            Let("f",
        #                Lambda("x", Identifier("g")),
        #                Apply(
        #                    Apply(Identifier("pair"),
        #                          Apply(Identifier("f"), Identifier("3"))
        #                          ),
        #                    Apply(Identifier("f"), Identifier("true"))))),
        #     Apply(Identifier("h"), Identifier("3"))),

        # Lambda("f", Lambda("x", Apply(Identifier("f"), Apply(Identifier("f"), Identifier("x"))))),
        # Lambda("f", Lambda("x", Apply(Apply(Identifier("add"), Identifier("x")), Identifier("f")))),

        # Apply(Apply(Identifier("mul"), TypeMcol(cols=3)),
        #       Apply(Apply(Identifier("add"), Identifier("f")), TypeMcol(cols=3))),

        # Apply(Apply(Identifier("mul"), TypeMfixed(rows=2, cols=3)),
        #       Apply(Apply(Identifier("mul"), Identifier("f")), TypeMfixed(rows=5, cols=6))),

        # Apply(Apply(Identifier("mul"), TypeMfixed(rows=2, cols=3)), TypeMfixed(rows=3, cols=6)),

        # M(2,3) + f**M(5,6)*M(6,3)
        # Apply(Apply(Identifier("add"), TypeMfixed(rows=2, cols=3)),
        #       Apply( Apply(Identifier("mul"), Apply(Apply(Identifier("mul"), Identifier("f")), TypeMfixed(rows=5, cols=6))),  TypeMfixed(rows=6, cols=3))),

        # Apply(Apply(Identifier("add"), TypeMfixed(rows=2, cols=3)),
        #       Apply(Apply(Identifier("mul"), Identifier("f")), TypeMfixed(rows=2, cols=3))),

        Apply(Apply(Identifier("add"), TypeMfixed(rows=2, cols=3)),
              Apply(Apply(Identifier("mul"), TypeMfixed(rows=2, cols=4)), Identifier("f"))),

        # Apply(Apply(Identifier("add"), Identifier("f")), Identifier("g")),

        # M(2,3) + f*M(5,6)*g
        # Apply(Apply(Identifier("add"), TypeMfixed(rows=2, cols=3)),
        #       Apply(Apply(Identifier("mul"), Apply(Apply(Identifier("mul"), Identifier("f")), TypeMfixed(rows=5, cols=6))),  Identifier("g"))),

        # Apply(Apply(Identifier("add"), TypeMfixed(rows=2, cols=3)), Identifier("f")),

        # Apply(Apply(Identifier("add"), Identifier("f")), TypeMcol(cols=3)),

        # Apply(Apply(Identifier("mul"), TypeMcol(cols=5)), Apply(Apply(Identifier("mul"), TypeMfixed(rows=5, cols=31)), TypeMfixed(rows=31, cols=12))),
        # Apply(Apply(Identifier("index"), Apply(Apply(Identifier("add"), TypeMcol(cols=3)), Apply(Apply(Identifier("add"), Identifier("f")), TypeMcol(cols=3)))), Identifier("4")),
        # Apply(Apply(Identifier("add"), MatrixFixedDouble), MatrixFixed),

        # Function composition
        # fn f (fn g (fn arg (f g arg)))
        # Lambda("f", Lambda("g", Lambda("arg", Apply(Identifier("g"), Apply(Identifier("f"), Identifier("arg"))))))
    ]

    # infer_exp(my_env, Apply(Identifier("zero"), Identifier("4")))
    # infer_exp(my_env, Let("f", Lambda("x", Identifier("x")), Apply(Identifier("f"), Identifier("4"))))
    # infer_exp(my_env, Let("y", Identifier("m"), Let("x", Apply(Identifier("y"), Identifier("4")), Identifier("x"))))
    # infer_exp(my_env, Lambda("m", Let("y", Identifier("m"), Let("x", Apply(Identifier("y"), Identifier("4")), Identifier("x")))))

    # log_content("Top env:")
    # for e in my_env:
    #     log_content("{}: {}".format(e, my_env[e]))
    # log_content("")

    # my_env["x3"] = TypeVariable()
    # infer_exp(my_env, Lambda("x", Lambda("y", Apply(Apply(Identifier("add"), Identifier("x3")), Identifier("3")))))
    for example in examples:
        ty_list, mgu_list, t_list = infer_exp(my_env, example)
        for cur_index in range(len(ty_list)):
            log_content("cur_index:{}".format(cur_index))
            ty = ty_list[cur_index]
            mgu = mgu_list[cur_index]
            t = t_list[cur_index]
            v_ty = apply(mgu, my_env['f'])

            if not check_final_mtype(v_ty):
                continue
            if isinstance(v_ty, TypeM):
                log_content("f, v_ty: {}, rows:{}, cols:{}, addr:{}".format(v_ty, v_ty.rows, v_ty.cols, id(v_ty)))
            else:
                log_content("f, v_ty: {}, addr:{}".format(v_ty, id(v_ty)))
            v_ty = apply(mgu, my_env['g'])
            if isinstance(v_ty, TypeM):
                log_content("g, v_ty: {}, rows:{}, cols:{}, addr:{}".format(v_ty, v_ty.rows, v_ty.cols, id(v_ty)))
            else:
                log_content("g, v_ty: {}, addr:{}".format(v_ty, id(v_ty)))
            log_content("ty:{}, ty.rows:{}, cols:{}, addr:{}".format(ty, ty.rows, ty.cols, id(ty)))
            # check_mul_list()


if __name__ == '__main__':
    main()
