from .mesh_eigen import *
from .mesh_matlab import *
from .mesh_numpy import *
from ..de_companion.geometry import GeometryType
from ..la_tools.la_helper import *


def get_gp_func_impl(name, gp_type=GeometryType.TRIANGLE, la_type=ParserTypeEnum.EIGEN):
    """
    Get the implementation code for builtin geometry processing functions
    :param name: function name
    :param gp_type: geometry type including mesh, point cloud, ...
    :param la_type: different backends
    :return: impl code
    """
    impl = ''
    if gp_type == GeometryType.TRIANGLE:
        if la_type == ParserTypeEnum.EIGEN:
            if name in MESH_EIGEN_DICT:
                impl = MESH_EIGEN_DICT[name]
    return impl