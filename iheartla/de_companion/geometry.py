from enum import Enum


class GeometryType(Enum):
    INVALID = -1
    TRIANGLE = 0
    POINT = 1


class CfgGeometry(object):
    def __init__(self, g_type=GeometryType.INVALID, dim=3):
        super().__init__()
        self.g_type = g_type
        self.dim = dim


class CfgTriangle(CfgGeometry):
    def __init__(self, v=None, e=None, f=None):
        super().__init__(GeometryType.TRIANGLE)
        self.v = v
        self.e = e
        self.f = f


class CfgPointCloud(CfgGeometry):
    def __init__(self, v=None):
        super().__init__(GeometryType.POINT)
        self.v = v
