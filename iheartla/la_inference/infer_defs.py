import copy
LOCAL_DEBUG = False
if LOCAL_DEBUG:
    from inference_logger import log_content, log_perm
else:
    from .inference_logger import log_content, log_perm


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


###############################################
# Type constants
###############################################
Integer = TypeOperator("int", [])    # Basic integer
Double = TypeOperator("double", [])  # Basic double
Bool = TypeOperator("bool", [])      # Basic bool
# Matrix definitions
Matrix = TypeM()
MatrixDouble = TypeMDouble()
MatrixRow = TypeMrow()
MatrixRowDouble = TypeMrowDouble()
MatrixCol = TypeMcol()
MatrixColDouble = TypeMcolDouble()
MatrixFixed = TypeMfixed()
MatrixFixedDouble = TypeMfixedDouble()


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


TOP_ENV = {
    "mul": [
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
    "add": [
        Function(Matrix, Function(Matrix, Matrix)),
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
        Function(Integer, Function(Integer, Integer))
    ],
    "index": [
        Function(Matrix, Function(Integer, Integer)),
        Function(MatrixDouble, Function(Integer, Double)),
        Function(MatrixRow, Function(Integer, Integer)),
        Function(MatrixRowDouble, Function(Integer, Double)),
        Function(MatrixCol, Function(Integer, Integer)),
        Function(MatrixColDouble, Function(Integer, Double)),
        Function(MatrixFixed, Function(Integer, Integer)),
        Function(MatrixFixedDouble, Function(Integer, Double))
    ],
}


###############################################
# dict operation
###############################################
def gen_env_dict(m_set):
    res = {}
    for m in m_set:
        res[m.name] = m
    return res


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