from tatsu.symtables import *


class LaSymbol(Symbol):
    def __init__(self, name, node, val_type, ignorecase=False, duplicates=False):
        super(LaSymbol, self).__init__(name=name, node=node, ignorecase=ignorecase, duplicates=duplicates)
        self._val_type = val_type

    @property
    def val_type(self):
        return self._val_type
