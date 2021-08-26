from enum import Enum, IntEnum, IntFlag
import copy
import math
LOCAL_DEBUG = False
if LOCAL_DEBUG:
    from infer_defs import *
else:
    from .infer_defs import *


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


# =======================================================#
# Type inference machinery


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
        elif type(x).__name__ == type(y).__name__ and x.name == y.name:
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