#!/usr/bin/env python
"""
.. module:: inference
   :synopsis: An implementation of the Hindley Milner type checking algorithm
              based on the code by Robert Smallshire.
"""

if __name__ == '__main__':
    from infer_hm import *
else:
    from .infer_hm import *


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


# ==================================================================#
def infer_exp(env, node):
    infer_ty_list = []
    new_gmu_list = []
    t_list = []
    env.update(TOP_ENV)
    log_perm("node info: {}".format(str(node)))
    log_content("Top env:")
    log_dict(env)
    log_content("")
    global add_fun_list, mul_fun_list
    add_fun_list.clear()
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
            log_content("total_index:{}".format(total_index))
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
                    log_content("cnt: {}, start".format(cnt))
                    # Handle addition
                    unresolved_add = handle_addition(new_gmu)
                    if unresolved_add:
                        unresolved = True
                    # Handle multiplication
                    unresolved_mul = handle_multiplication(new_gmu)
                    if unresolved_mul:
                        unresolved = True
                    # log_content("ty:{}, ty.rows:{}, cols:{}, addr:{}".format(infer_ty, infer_ty.rows, infer_ty.cols, id(infer_ty)))
                    log_content("cnt: {}, unresolved:{}".format(cnt, unresolved))
                    cnt += 1
                    if cnt > 5:
                        unresolved = False
                    # if cnt < 5:
                    #     unresolved = False
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


def resolved_type(value):
    is_resolved = True
    if isinstance(value, TypeM):
        is_resolved = resolved_matrix(value)
    elif isinstance(value, TypeV):
        is_resolved = resolved_vector(value)
    return is_resolved


def resolved_matrix(m_value):
    is_resolved = True
    if isinstance(m_value, TypeMrowDouble) or isinstance(m_value, TypeMrow):
        is_resolved = m_value.rows is not None
    elif isinstance(m_value, TypeMcolDouble) or isinstance(m_value, TypeMcol):
        is_resolved = m_value.cols is not None
    elif isinstance(m_value, TypeMfixedDouble) or isinstance(m_value, TypeMfixed):
        is_resolved = (m_value.cols is not None) and (m_value.rows is not None)
    return is_resolved


def resolved_vector(m_value):
    is_resolved = True
    if isinstance(m_value, TypeVfixed) or isinstance(m_value, TypeVfixedDouble):
        is_resolved = m_value.rows is not None
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
            if isinstance(value, TypeM) or isinstance(value, TypeV):
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
            log_content("add_index:, unresolved:{}\n"
                        "fir param:{}, rows:{}, cols:{}, addr:{};\n"
                        "sec param:{}, rows:{}, cols:{}, addr:{};\n"
                        "ret param:{}, rows:{}, cols:{}, addr:{};\n".format(unresolved,
                                                                            first_param, first_param.rows,
                                                                            first_param.cols, id(first_param),
                                                                            sec_param, sec_param.rows, sec_param.cols,
                                                                            id(sec_param),
                                                                            ret_param, ret_param.rows, ret_param.cols,
                                                                            id(ret_param)))
        elif isinstance(first_param, TypeV):
            # vector addition
            remain_func = get_param(new_gmu, var_fun.types[1])
            sec_param = get_param(new_gmu, remain_func.types[0])
            ret_param = get_param(new_gmu, remain_func.types[1])
            assert isinstance(sec_param, TypeV)
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
            resolved = resolved_vector(ret_param)
            if not (resolved and resolved_vector(first_param) and resolved_vector(sec_param)):
                unresolved = True
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
            # matrix multiply
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
                        assert ret_param.cols == sec_param.cols
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
            elif isinstance(sec_param, TypeV):
                # Matrix * Vector
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
        elif isinstance(first_param, TypeV):
            # Vector * Scalar
            if ret_param.rows is None:
                ret_param.rows = first_param.rows
            else:
                if first_param.rows is None:
                    # Fill back
                    first_param.rows = ret_param.rows
                else:
                    assert first_param.rows == ret_param.rows
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
            elif isinstance(sec_param, TypeV):
                # Scalar * Vector
                if ret_param.rows is None:
                    ret_param.rows = sec_param.rows
                else:
                    if sec_param.rows is None:
                        # Fill back
                        sec_param.rows = ret_param.rows
                    else:
                        assert sec_param.rows == ret_param.rows
            else:
                # Scalar * Scalar
                pass
        resolved = resolved_type(ret_param)
        if not (resolved and resolved_type(first_param) and resolved_type(sec_param)):
            unresolved = True
        log_content("unresolved:{};\n".format(unresolved))
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

        # Apply(Apply(Identifier("add"), TypeMfixed(rows=2, cols=3)),
        #       Apply(Apply(Identifier("mul"), TypeMfixed(rows=2, cols=4)), Identifier("f"))),

        # Apply(Apply(Identifier("add"), Identifier("f")), Identifier("g")),

        # M(2,3) + f*M(5,6)*g
        # Apply(Apply(Identifier("add"), TypeMfixed(rows=2, cols=3)),
        #       Apply(Apply(Identifier("mul"), Apply(Apply(Identifier("mul"), Identifier("f")), TypeMfixed(rows=5, cols=6))),  Identifier("g"))),

        Apply(Apply(Apply(Identifier("index"), TypeMfixedDouble(rows=2, cols=3)),
              Apply(Apply(Apply(Identifier("index"), Apply(Apply(Identifier("add"), TypeMfixed(rows=2, cols=3)),
                                                     Apply(Apply(Identifier("mul"),
                                                                 Apply(Apply(Identifier("mul"), Identifier("f")),
                                                                       TypeMfixed(rows=5, cols=6))), Identifier("g")))),
                    Identifier("23")),Identifier("23"))), Identifier("23")),

        # Apply(Apply(Identifier("index"), TypeMfixedDouble(rows=2, cols=3)),
        #             Identifier("23")),

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
    valid_cnt = 0
    for example in examples:
        ty_list, mgu_list, t_list = infer_exp(my_env, example)
        for cur_index in range(len(ty_list)):
            ty = ty_list[cur_index]
            mgu = mgu_list[cur_index]
            t = t_list[cur_index]
            f_ty = apply(mgu, my_env['f'])
            g_ty = apply(mgu, my_env['g'])
            if not check_final_mtype(f_ty):
                continue
            if not check_final_mtype(g_ty):
                continue
            log_content("valid_cnt:{}, mgu:{}".format(valid_cnt, mgu))
            valid_cnt += 1
            if isinstance(f_ty, TypeM):
                log_content("f, v_ty: {}, rows:{}, cols:{}, addr:{}".format(f_ty, f_ty.rows, f_ty.cols, id(f_ty)))
            else:
                log_content("f, v_ty: {}, addr:{}".format(f_ty, id(f_ty)))
            if isinstance(g_ty, TypeM):
                log_content("g, v_ty: {}, rows:{}, cols:{}, addr:{}".format(g_ty, g_ty.rows, g_ty.cols, id(g_ty)))
            else:
                log_content("g, v_ty: {}, addr:{}".format(g_ty, id(g_ty)))
            # result
            if isinstance(ty, TypeM):
                log_content("ty:{}, ty.rows:{}, cols:{}, addr:{}".format(ty, ty.rows, ty.cols, id(ty)))
            else:
                log_content("ty:{}, addr:{}".format(ty, id(ty)))
            # check_mul_list()


if __name__ == '__main__':
    main()
