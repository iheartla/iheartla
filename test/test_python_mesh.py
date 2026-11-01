import sys
sys.path.append('./')
import io
import os
import contextlib
import unittest
import numpy as np
from iheartla.la_parser.parser import compile_la_content, ParserTypeEnum

# Generated NumPy code for I❤️MESH programs does `from triangle_mesh import *`.
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'iheartla', 'mesh', 'Python'))
from triangle_mesh import TriangleMesh


class TestMesh(unittest.TestCase):
    def test_generated_numpy_runs_with_mesh_runtime(self):
        # ElementSets and indicator() are provided by the Python mesh runtime, and Edges(f) is a set of
        # edges: Vertices(Edges(f)) used to pick the face overload and index faces with edge indices.
        la_str = """ElementSets from MeshConnectivity
        Vertices, Edges from FundamentalMeshAccessors(M)
        EdgeIndex, VertexOneRing from Neighborhoods(M)
        M ∈ FaceMesh
        V, E, F = ElementSets(M)
        n(f) = |Edges(f)| where f ∈ F
        d(f) = |Vertices(Edges(f))| where f ∈ F
        m(v) = |Edges(v)| where v ∈ V
        e(i, j) = EdgeIndex(i, j) where i, j ∈ V
        r(v) = |VertexOneRing(v)| where v ∈ V"""
        with contextlib.redirect_stdout(io.StringIO()):
            result = compile_la_content(la_str, ParserTypeEnum.NUMPY)
        namespace = {}
        exec(result[ParserTypeEnum.NUMPY], namespace)
        #   0 --- 2
        #   |  /  |
        #   1 --- 3
        mesh = TriangleMesh(np.array([[0, 1, 2], [1, 3, 2]]))
        h = namespace['heartlib'](mesh)
        self.assertEqual([h.n(f) for f in (0, 1)], [3, 3])
        self.assertEqual([h.d(f) for f in (0, 1)], [3, 3])
        self.assertEqual([h.m(v) for v in (0, 1, 2, 3)], [2, 3, 3, 2])
        # EdgeIndex intersects sets from the runtime's nonzeros(), which must be frozensets
        self.assertEqual([h.e(i, j) for (i, j) in [(0, 1), (0, 2), (1, 2), (1, 3), (2, 3)]], [0, 1, 2, 3, 4])
        self.assertEqual([h.r(v) for v in (0, 1, 2, 3)], [2, 3, 3, 2])

    def test_runtime_element_sets(self):
        tri = TriangleMesh(np.array([[0, 1, 2], [1, 3, 2]]))
        V, E, F = tri.ElementSets()
        self.assertEqual((len(V), len(E), len(F)), (4, 5, 2))
        self.assertEqual([m.shape for m in tri.BoundaryMatrices()], [(4, 5), (5, 2)])
        tet = TriangleMesh(np.array([[0, 1, 2, 3]]))
        V, E, F, C = tet.ElementSets()
        self.assertEqual((len(V), len(E), len(F), len(C)), (4, 6, 4, 1))
        self.assertEqual([m.shape for m in tet.BoundaryMatrices()], [(4, 6), (6, 4), (4, 1)])
        self.assertEqual(len(tet.UnsignedBoundaryMatrices()), 3)
        # the boundary of a boundary is empty
        for mesh in (tri, tet, TriangleMesh(np.array([[0, 1, 2, 3], [1, 2, 3, 4]]))):
            B = mesh.BoundaryMatrices()
            for k in range(len(B) - 1):
                self.assertEqual(abs(B[k] @ B[k + 1]).sum(), 0)
