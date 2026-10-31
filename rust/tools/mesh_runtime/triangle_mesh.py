"""The I❤️MESH Python runtime, completed with what generated code calls.

Generated NumPy code does `from triangle_mesh import *` and calls
`M.ElementSets()` and `indicator(S, n)`, which `iheartla/mesh/Python/
triangle_mesh.py` does not define (it has `MeshSets()` and per-kind
`*_to_vector` methods). This module re-exports that runtime and adds both.
Put this directory first on `sys.path` when running generated code.
"""
import importlib.util
import os
import sys

import numpy as np
import scipy.sparse

_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'iheartla', 'mesh', 'Python')
sys.path.insert(0, os.path.abspath(_DIR))  # for its `from util import *`
_spec = importlib.util.spec_from_file_location('_iheartmesh_triangle_mesh', os.path.join(_DIR, 'triangle_mesh.py'))
_orig = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_orig)

for _name in dir(_orig):
    if not _name.startswith('__'):
        globals()[_name] = getattr(_orig, _name)


def _element_sets(self):
    sets = [frozenset(self.Vi), frozenset(self.Ei), frozenset(self.Fi)]
    if self.T.shape[1] == 4:  # a tetrahedral mesh
        sets.append(frozenset(self.Ti))
    return sets


TriangleMesh.ElementSets = _element_sets


def indicator(s, n):
    """The indicator vector (n×1, sparse) of a set of element indices."""
    s = sorted(s)
    return scipy.sparse.coo_matrix((np.ones(len(s), dtype=int), (s, np.zeros(len(s), dtype=int))), shape=(n, 1), dtype=int).tocsr()


def nonzeros(target):
    return frozenset(int(i) for i in target.nonzero()[0])
