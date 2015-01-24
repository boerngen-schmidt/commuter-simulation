"""
Created on 29.09.2014

@author: Benjamin
"""
import math
import time
import logging
from multiprocessing import Process, JoinableQueue, Queue

from builder.enums import PointType
from builder.commands import PointCreationCommand
from helper.counter import Counter
import numpy as np
from psycopg2.extras import NamedTupleCursor
from shapely.geometry import Polygon, Point, box, shape
from database import connection as db
from shapely.wkb import loads


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

    def set_t(self, t):
        """Tuning Parameter

        Based on t the function decides wether the polygon should be further split or not
        :param float t: Parameter for tuning the SRS function
        """
        if 2 >= t >= 1:
            self.t = t
        else:
            raise ValueError('Value for t should be between 1 and 2')

    def run(self):
        execute_statement = 'EXECUTE de_sim_points_{type!s}_plan ({rs!r}, \'\\x{point!s}\'::bytea);'

        while True:
            generation_start = time.time()
            cmd = self.queue.get()
            if not cmd:
                break
            assert isinstance(cmd, PointCreationCommand)

            # Get all the residential stuff

            # Choose the right sql based on the point type
            landuse = 'landuse = \'residential\''
            if cmd.point_type in (PointType.End, PointType.Within_End):
                landuse += ' OR landuse =\'industrial\''

            # Choose right de_shp table based on rs
            if len(cmd.rs) is 12:
                shp = 'gemeinden'
            else:
                shp = 'kreise'

            # Replace this polygon with a query from the database with the residential areas
            with db.get_connection() as conn:
                cur = conn.cursor(cursor_factory=NamedTupleCursor)
                sql = 'CREATE TEMPORARY TABLE living_areas ON COMMIT DROP AS ' \
                      'SELECT ' \
                      ' way as geom, ' \
                      ' CASE WHEN p.landuse = \'residential\' THEN (%(w)s*ST_Area(way)) ELSE ST_Area(way) END AS area '\
                      'FROM de_osm_polygon p ' \
                      'INNER JOIN de_shp_{shp!s} s ON (s.rs = %(rs)s AND ST_Within(p.way, s.geom)) ' \
                      'WHERE {landuse!s}'
                args = dict(rs=cmd.rs, w=0.5)
                cur.execute(sql.format(shp=shp, landuse=landuse), args)     # created temporary table

                sql = 'SELECT SUM(ST_Area(geom)) FROM living_areas'
                cur.execute(sql)
                total_area, = cur.fetchone()

                sql = 'SELECT ST_AsEWKB(geom) AS geom_b, area FROM living_areas'
                cur.execute(sql)
                areas = cur.fetchall()

            created_points = 0
            for area in areas:
                polygon = loads(bytes(area.geom_b))
                num_points = int(math.floor(cmd.num_points * area.area / total_area))
                rs = cmd.rs
                points = self._generate_points(polygon, num_points)
                created_points += len(points)

                [self.output.put(execute_statement.format(rs=rs, type=cmd.point_type, point=p.wkb_hex))
                 for p in points]

            generation_time = time.time() - generation_start
            num = self.counter.increment()
            self.logging.info('(%4d/%d) %s: Created %s points for "%s". Generation time: %s',
                              num, self.total,
                              self.name, created_points, cmd.name,
                              generation_time)

        self.logging.info('Exiting %s', self.name)
        self.output.close()

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