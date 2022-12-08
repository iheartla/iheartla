

class LocalFuncData(object):
    def __init__(self, name=''):
        super().__init__()
        self.name = name  # function name
        self.params_data = ParamsData()


class ParamsData(object):
    def __init__(self):
        super().__init__()
        self.arith_dim_list = []
        self.same_dim_list = []
        self.subscripts = {}
        self.sub_name_dict = {}
        self.dim_dict = {}        # parameter used. h:w_i
        self.seq_dim_dict = {}    # support repeated symbol
        self.dim_seq_set = set()  # sequence of dimension for ragged list
        self.ids_dict = {}    # identifiers with subscripts
        self.parameters = []  #
        self.symtable = {}    # for params only
        self.set_checking = {}  # check key is a member of value

    def update_dim_dict(self, dim, target, pos):
        if dim in self.dim_seq_set:
            # can repeat
            if dim not in self.seq_dim_dict:
                self.seq_dim_dict[dim] = {}
            if target not in self.seq_dim_dict[dim]:
                self.seq_dim_dict[dim][target] = []
            self.seq_dim_dict[dim][target].append(pos)
        if dim not in self.dim_dict:
            self.dim_dict[dim] = {}
        self.dim_dict[dim][target] = pos

    def remove_dim(self, dim, target):
        if dim in self.dim_dict:
            self.dim_dict[dim].pop(target, None)
            if len(self.dim_dict[dim]) == 0:
                del self.dim_dict[dim]

    def remove_target_from_dim_dict(self, target):
        for key in self.dim_dict.keys():
            if target in self.dim_dict[key]:
                del self.dim_dict[key][target]
                if len(self.dim_dict[key]) == 0:
                    del self.dim_dict[key]
                break

    def reset(self):
        self.arith_dim_list.clear()
        self.same_dim_list.clear()
        self.subscripts.clear()
        self.sub_name_dict.clear()
        self.dim_dict.clear()
        self.seq_dim_dict.clear()
        self.dim_seq_set.clear()
        self.ids_dict.clear()
        self.parameters.clear()
        self.symtable.clear()
        self.set_checking.clear()