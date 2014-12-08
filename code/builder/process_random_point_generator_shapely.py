"""
Created on 29.09.2014

@author: Benjamin
"""
import math
import time
import logging
from multiprocessing import Process, Value, JoinableQueue, Queue

import numpy as np
import pylab
from shapely.geometry import Polygon, Point, box, shape


class Counter(object):
    def __init__(self):
        self.val = Value('i', 0)

    def increment(self, n=1):
        with self.val.get_lock():
            self.val.value += n
            result = self.value
        return result

    @property
    def value(self):
        return self.val.value


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


class PointCreatorProcess(Process):
    """
    Creates new routing start and destination points for the simulation.

    As basis for how many points should be created within a district,
    the data from the Zensus 2011 should be used.
    """

    def __init__(self, info_queue: Queue, output_queue: JoinableQueue, counter: Counter):
        """

        :param info_queue:
        :param multiprocessing.queue.Queue output_queue:
        :param Counter counter: Ze Counter class for counting counts
        """
        Process.__init__(self)
        self.queue = info_queue
        self.output = output_queue
        self.counter = counter

        self.logging = logging.getLogger(self.name)
        self.total = info_queue.qsize()
        self.t = 2
        self.plot = False

    def set_t(self, t):
        """Tuning Parameter

        :param float t: Parameter for tuning the SRS function
        """
        if 2 >= t >= 1:
            self.t = t
        else:
            raise ValueError('Value for t should be between 1 and 2')

    def run(self):
        execute_statement = 'EXECUTE de_sim_points_{type!s}_plan ({rs!r}, \'\\x{point!s}\'::bytea);'

        while not self.queue.empty():
            generation_start = time.time()
            cmd = self.queue.get()
            assert isinstance(cmd, PointCreationCommand)

            if cmd.polygon.area <= 0 or cmd.num_points <= 0:
                num = self.counter.increment()
                self.logging.info(
                    '(%4d/%d) %s: Skipped creating points for "%s". Polygon Area: %s, Number of Point: %s',
                    num, self.total, self.name, cmd.name, cmd.polygon.area, cmd.num_points)
                del cmd
                continue

            rs = cmd.rs
            points = self._generate_points(cmd.polygon, cmd.num_points)

            if self.plot:
                pylab.figure(num=None, figsize=(20, 20), dpi=200)
                self._plot_polygon(cmd.polygon)

                # Plot the generated points
                pylab.plot([p.x for p in points], [p.y for p in points], 'bs', alpha=0.75)

                # Write the number of patches and the total patch area to the figure
                pylab.text(-25, 25, "Patches: %d, total area: %.2f" % (1, cmd.polygon.area, ))

                pylab.savefig('{rs}.png'.format(rs=rs))

            [self.output.put(execute_statement.format(rs=rs, type=cmd.type_points, point=p.wkb_hex)) for p in points]

            generation_time = time.time() - generation_start
            num = self.counter.increment()
            self.logging.info('(%4d/%d) %s: Created %s points for "%s". Generation time: %s',
                              num, self.total,
                              self.name, len(points), cmd.name,
                              generation_time)
            del points, cmd
            time.sleep(0.5)  # Sleep for 500ms

        self.logging.info('Exiting %s', self.name)
        self.output.close()

    def _plot_polygon(self, polygon):
        if polygon.geom_type is 'MultiPolygon':
            for patch in polygon.geoms:
                self._plot_polygon(patch)
            return

        assert polygon.geom_type in ['Polygon']
        assert polygon.is_valid

        # Fill and outline each patch
        x, y = polygon.exterior.xy
        pylab.fill(x, y, color='#FFFFFF', aa=True)
        pylab.plot(x, y, color='#666666', aa=True, lw=1.0)

        # Do the same for the holes of the patch
        for hole in polygon.interiors:
            x, y = hole.xy
            pylab.fill(x, y, color='#ffffff', aa=True)
            pylab.plot(x, y, color='#999999', aa=True, lw=1.0)

    def _generate_points(self, polygon: Polygon, n) -> list:
        """Generates sample points within a given geometry

        :param shapely.geometry.Polygon polygon: the polygon to create points in
        :param int n: Number of points to generate in polygon
        :return: A list with point in the polygon
        :rtype: list[Point]
        """
        if n <= 0:
            return []

        if polygon.area <= 0:
            return []

        # # DEBUG Plot
        # pylab.figure(num=None, figsize=(20, 20), dpi=400)
        # self._plot_polygon(polygon)
        # pylab.savefig('{n}.png'.format(n=n))
        # pylab.close()

        bbox = polygon.envelope
        """(minx, miny, maxx, maxy) bbox"""
        if (polygon.area * self.t) < bbox.area:
            if (bbox.bounds[2] - bbox.bounds[0]) > (bbox.bounds[3] - bbox.bounds[1]):
                bbox_1 = box(*self._bbox_left(bbox.bounds))
                bbox_2 = box(*self._bbox_right(bbox.bounds))
            else:
                bbox_1 = box(*self._bbox_bottom(bbox.bounds))
                bbox_2 = box(*self._bbox_top(bbox.bounds))

            p1 = shape(polygon)
            p1 = p1.difference(bbox_1)

            p2 = shape(polygon)
            p2 = p2.difference(bbox_2)

            del bbox_1, bbox_2
            # k = bisect.bisect_left(u, p1.area / polygon.area)
            k = int(round(n * (p1.area / polygon.area)))

            v = self._generate_points(p1, k) + self._generate_points(p2, n - k)
            del polygon, p1, p2
        else:
            v = []
            max_iterations = self.t * n + 5 * math.sqrt(self.t * n)
            v_length = len(v)
            while v_length < n and max_iterations > 0:
                max_iterations -= 1
                v.append(self._random_point_in_polygon(polygon))
                v_length = len(v)

            if len(v) < n:
                raise Exception('Too many iterations')

            self.logging.debug('Generated %s points', n)

        del bbox
        return v

    def _random_point_in_polygon(self, polygon):
        """Returns random point in polygon

        :param Polygon poly:
        :return: A random point
        :rtype: Point
        """
        (minx, miny, maxx, maxy) = polygon.bounds
        while True:
            p = Point(np.random.uniform(minx, maxx), np.random.uniform(miny, maxy))
            if polygon.contains(p):
                return p

    def _bbox_left(self, bbox):
        """Returns left half of bbox"""
        l = (bbox[2] - bbox[0]) / 2
        return bbox[0], bbox[1], bbox[2] - l, bbox[3]

    def _bbox_right(self, bbox):
        """Returns right half of bbox"""
        l = (bbox[2] - bbox[0]) / 2
        return bbox[0] + l, bbox[1], bbox[2], bbox[3]

    def _bbox_top(self, bbox):
        """Returns top half of bbox"""
        l = (bbox[3] - bbox[1]) / 2
        return bbox[0], bbox[1] + l, bbox[2], bbox[3]

    def _bbox_bottom(self, bbox):
        """Returns bottom half of bbox"""
        l = (bbox[3] - bbox[1]) / 2
        return bbox[0], bbox[1], bbox[2], bbox[3] - l