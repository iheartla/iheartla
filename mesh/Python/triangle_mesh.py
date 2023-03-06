import numpy as np
import scipy
import scipy.linalg
from scipy import sparse
from util import *


def nonzeros(target):
    return set(target.nonzero()[0])


class TriangleMesh:
    def __init__(self, T):
        self.V = None
        self.E = None
        self.F = None
        self.T = None
        self.Vi = None
        self.Ei = None
        self.Fi = None
        self.Ti = None
        self.bm1 = None
        self.bm2 = None
        self.bm3 = None
        self.pos_bm1 = None
        self.pos_bm2 = None
        self.pos_bm3 = None
        self.map_f = {}
        self.map_e = {}
        self.initialize(T)

    def initialize(self, T):
        self.V = range(np.amax(T) + 1)
        self.T = preprocess_matrix(T)
        if T.shape[1] == 4:
            # tets
            self.create_faces()
            self.create_edges()
            self.build_boundary_mat1()
            self.build_boundary_mat2()
            self.build_boundary_mat3()
        elif T.shape[1] == 3:
            # faces
            self.F = T
            self.create_edges()
            self.build_boundary_mat1()
            self.build_boundary_mat2()
        self.init_mesh_indices()

    def init_mesh_indices(self):
        self.Vi = set(self.V)
        self.Ei = set([i for i in range(self.E.shape[0])])
        self.Fi = set([i for i in range(self.F.shape[0])])
        self.Ti = set([i for i in range(self.T.shape[0])])

    def create_edges(self):
        E = np.zeros((3 * self.F.shape[0], 2), dtype=int)
        for i in range(self.F.shape[0]):
            E[3 * i, :] = sort_vector([self.F[i, 0], self.F[i, 1]])
            E[3 * i + 1, :] = sort_vector([self.F[i, 0], self.F[i, 2]])
            E[3 * i + 2, :] = sort_vector([self.F[i, 1], self.F[i, 2]])
        self.E = np.asarray(remove_duplicate_rows(sort_matrix(E)), dtype=int)
        for i in range(self.E.shape[0]):
            self.map_e[self.edge_key(self.E[i, 0], self.E[i, 1])] = i

    def create_faces(self):
        F = np.zeros((4*self.T.shape[0], 3), dtype=int)
        for i in range(self.T.shape[0]):
            F[4 * i, :] = sort_vector([self.T[i, 0], self.T[i, 1], self.T[i, 2]])
            F[4 * i + 1, :] = sort_vector([self.T[i, 0], self.T[i, 1], self.T[i, 3]])
            F[4 * i + 2, :] = sort_vector([self.T[i, 0], self.T[i, 2], self.T[i, 3]])
            F[4 * i + 3, :] = sort_vector([self.T[i, 1], self.T[i, 2], self.T[i, 3]])
        self.F = np.asarray(remove_duplicate_rows(sort_matrix(F)), dtype=int)
        for i in range(self.F.shape[0]):
            self.map_f[self.face_key(self.F[i, 0], self.F[i, 1], self.F[i, 2])] = i

    def face_key(self, i, j, k):
        return hash("i{}j{}k{}".format(i, j, k))

    def edge_key(self, i, j):
        return hash("i{}j{}".format(i, j))

    def get_face_index(self, i, j, k):
        sign = -1
        p = permute_rvector([i, j, k])
        key = self.face_key(p[0], p[1], p[2])
        if key in self.map_f:
            sign = 1
            return self.map_f[key], sign
        return self.map_f[self.face_key(p[0], p[2], p[1])], sign

    def get_edge_index(self, i, j):
        sign = -1
        if i < j:
            sign = 1
            return self.map_e[self.edge_key(i, j)], sign
        return self.map_e[self.edge_key(j, i)], sign

    def build_boundary_mat1(self):
        index_list = []
        value_list = []
        for i in range(self.E.shape[0]):
            index_list.append((self.E[i, 0], i))
            value_list.append(-1)
            index_list.append((self.E[i, 1], i))
            value_list.append(1)
        self.bm1 = scipy.sparse.coo_matrix((value_list, np.asarray(index_list).T), shape=(len(self.V), self.E.shape[0]), dtype=int)
        self.pos_bm1 = scipy.sparse.coo_matrix(([abs(v) for v in value_list], np.asarray(index_list).T), shape=(len(self.V), self.E.shape[0]), dtype=int)


    def build_boundary_mat2(self):
        index_list = []
        value_list = []
        for i in range(self.F.shape[0]):
            idx, sign = self.get_edge_index(self.F[i, 0], self.F[i, 1])
            index_list.append((idx, i))
            value_list.append(sign)
            idx, sign = self.get_edge_index(self.F[i, 0], self.F[i, 2])
            index_list.append((idx, i))
            value_list.append(-sign)
            idx, sign = self.get_edge_index(self.F[i, 1], self.F[i, 2])
            index_list.append((idx, i))
            value_list.append(sign)
        self.bm2 = scipy.sparse.coo_matrix((value_list, np.asarray(index_list).T), shape=(self.E.shape[0], self.F.shape[0]), dtype=int)
        self.pos_bm2 = scipy.sparse.coo_matrix(([abs(v) for v in value_list], np.asarray(index_list).T), shape=(self.E.shape[0], self.F.shape[0]), dtype=int)


    def build_boundary_mat3(self):
        index_list = []
        value_list = []
        for i in range(self.T.shape[0]):
            idx, sign = self.get_face_index(self.T[i, 0], self.T[i, 1], self.T[i, 2])
            index_list.append((idx, i))
            value_list.append(-sign)
            idx, sign = self.get_face_index(self.T[i, 0], self.T[i, 1], self.T[i, 3])
            index_list.append((idx, i))
            value_list.append(sign)
            idx, sign = self.get_face_index(self.T[i, 0], self.T[i, 2], self.T[i, 3])
            index_list.append((idx, i))
            value_list.append(-sign)
            idx, sign = self.get_face_index(self.T[i, 1], self.T[i, 2], self.T[i, 3])
            index_list.append((idx, i))
            value_list.append(sign)
        self.bm3 = scipy.sparse.coo_matrix((value_list, np.asarray(index_list).T), shape=(self.F.shape[0], self.T.shape[0]), dtype=int)
        self.pos_bm3 = scipy.sparse.coo_matrix(([abs(v) for v in value_list], np.asarray(index_list).T), shape=(self.F.shape[0], self.T.shape[0]), dtype=int)

    def n_vertices(self):
        return len(self.Vi)

    def n_edges(self):
        return len(self.Ei)

    def n_faces(self):
        return len(self.Fi)

    def n_tets(self):
        return len(self.Ti)

    def nonzeros(self, target):
        return set(target.nonzero()[0])

    def MeshSets(self):
        return [self.Vi, self.Ei, self.Fi]

    def BoundaryMatrices(self):
        return [self.bm1, self.bm2]

    def UnsignedBoundaryMatrices(self):
        return [self.pos_bm1, self.pos_bm2]

    def vertices_to_vector(self, vset):
        index_list = []
        value_list = []
        for v in vset:
            index_list.append((v, 0))
            value_list.append(1)
        return scipy.sparse.coo_matrix((value_list, np.asarray(index_list).T), shape=(len(self.V), 1), dtype=int)

    def edges_to_vector(self, eset):
        index_list = []
        value_list = []
        for e in eset:
            index_list.append((e, 0))
            value_list.append(1)
        return scipy.sparse.coo_matrix((value_list, np.asarray(index_list).T), shape=(self.E.shape[0], 1), dtype=int)

    def faces_to_vector(self, fset):
        index_list = []
        value_list = []
        for f in fset:
            index_list.append((f, 0))
            value_list.append(1)
        return scipy.sparse.coo_matrix((value_list, np.asarray(index_list).T), shape=(self.F.shape[0], 1), dtype=int)

    def tets_to_vector(self, tset):
        index_list = []
        value_list = []
        for t in tset:
            index_list.append((t, 0))
            value_list.append(1)
        return scipy.sparse.coo_matrix((value_list, np.asarray(index_list).T), shape=(self.T.shape[0], 1), dtype=int)


if __name__ == '__main__':
    #       2
    #     / | \
    #    0  |  3
    #     \ | /
    #       1
    # v, f = igl.read_triangle_mesh("/Users/pressure/Downloads/sphere.obj")
    T = np.asarray([[0,1,2,3], [1,2,3,4]])
    P = np.asarray([[1, 1, 1], [1, 2, 3], [2, 1, 4], [3, 1, 2]])
    tri = TriangleMesh(T)
    # print(tri.V)
    # print(tri.E)
    # print(tri.F)
    # print(tri.T)
    # print(tri.pos_bm1)
    # print(tri.Ei)
    # print(tri.Fi)
    a = tri.bm1 * tri.edges_to_vector({2})
    # print(a)
    print(tri.nonzeros(a))

