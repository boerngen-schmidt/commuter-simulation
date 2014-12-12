__author__ = 'Benjamin'


class PointCreationCommand(object):
    __slots__ = ['_rs', '_polygon', '_num_points', '_name', '_type_points']
    def __init__(self, rs: str, name: str, polygon: Polygon, points: int, point_type: str):
        self._rs = rs
        self._polygon = polygon
        self._num_points = points
        self._name = name
        self._type_points = point_type

    @property
    def rs(self):
        return self._rs

    @rs.setter
    def rs(self, value):
        self._rs = value

    @property
    def polygon(self):
        return self._polygon

    @polygon.setter
    def polygon(self, value):
        self._polygon = value

    @property
    def num_points(self):
        return self._num_points

    @num_points.setter
    def num_points(self, value):
        self._type_points = value

    @property
    def type_points(self):
        return self._type_points

    @type_points.setter
    def type_points(self, value):
        self._num_points = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value


class PointMatchCommand(object):
    __slots__ = ['_data', '_matching_type']

    def __init__(self, point_id, rs, data, matching_type, geometry):
        self._data = dict({'start': point_id, 'rs': rs, 'geom': geometry}, **data)
        self._matching_type = matching_type

    @property
    def point_id(self):
        return self._data['start']

    @property
    def geom(self):
        return self._data['geom']

    @property
    def rs(self):
        return self._data['rs']

    @property
    def data(self):
        return self._data

    @property
    def matching_type(self):
        return self._matching_type


class PointsMatchCommand(object):
    __slots__ = ['_point_id', '_rs', '_matching_type']

    def __init__(self, point_id, rs, matching_type):
        self._point_id = point_id
        self._rs = rs
        self._matching_type = matching_type

    @property
    def point_id(self):
        return self._point_id

    @property
    def rs(self):
        return self._rs

    @property
    def matching_type(self):
        return self._matching_type