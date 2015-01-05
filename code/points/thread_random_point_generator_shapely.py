"""
Created on 29.09.2014

@author: Benjamin
@obsolete
"""
import threading
import math
import time
import logging

from database import connection
import numpy.random as npr
import pylab
from shapely.geometry import Polygon, Point, box, shape
from shapely.wkb import loads
from psycopg2.extras import NamedTupleCursor


COUNTER_LOCK = threading.Lock()

counter = 0


class PointCreator(threading.Thread):
    """
    Creates new routing start and destination points for the simulation.

    As basis for how many points should be created within a district,
    the data from the Zensus 2011 should be used.
    """

    def __init__(self, name, info_queue, kreise=True, start_points=True):
        """Constructor

        :param str name: Name of the Thread
        :param queue.Queue info_queue; Reference to the Queue with information
        :param bool kreise: True to create points within
        """
        threading.Thread.__init__(self)
        self.setName(name)
        self.queue = info_queue
        self.kreise = kreise

        self.logging = logging.getLogger(name)
        self._get_total()
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
        # sql = 'WITH area AS (SELECT c.*, s.geom FROM de_commuter_{tbl} c JOIN de_shp_{tbl} s ON c.rs = s.rs WHERE c.rs={rs}) '
        # sql += 'INSERT INTO de_sim_points (parent_geometry, point_type, geom) SELECT area.rs , \'{type}\', RandomPointsInPolygon(area.geom, (area.outgoing + area.within)) FROM area '
        sql = 'SELECT c.*, ST_AsEWKB(s.geom) AS geom_b, ST_Area(s.geom) AS area FROM de_commuter_{tbl} c JOIN de_shp_{tbl} s ON c.rs = s.rs WHERE c.rs=\'{rs}\''

        if self.kreise:
            tbl = 'kreise'
        else:
            tbl = 'gemeinden'

        while not self.queue.empty():
            generation_start = time.time()
            rs = self.queue.get()
            with connection.get_connection() as con:
                cur = con.cursor(cursor_factory=NamedTupleCursor)
                cur.execute(sql.format(rs=rs, tbl=tbl))

                if cur.rowcount > 1:
                    records = cur.fetchall()
                    cur.execute(
                        'SELECT SUM(ST_Area(geom)) as total_area FROM de_shp_{tbl} WHERE rs=\'{rs}\';'.format(tbl=tbl,
                                                                                                              rs=rs))
                    total_area = cur.fetchone().total_area

                    points = []
                    for rec in records:
                        n = int(round(rec.outgoing * (rec.area / total_area)))
                        polygon = loads(bytes(rec.geom_b))
                        points += self._generate_points(polygon, n)
                else:
                    rec = cur.fetchone()
                    polygon = loads(bytes(rec.geom_b))
                    points = self._generate_points(polygon, rec.outgoing)

                generation_time = time.time() - generation_start

                if self.plot:
                    pylab.figure(num=None, figsize=(20, 20), dpi=200)
                    self._plot_polygon(polygon)

                    # Plot the generated points
                    pylab.plot([p.x for p in points], [p.y for p in points], 'bs', alpha=0.75)

                    # Write the number of patches and the total patch area to the figure
                    pylab.text(-25, 25,
                               "Patches: %d, total area: %.2f" % (len(polygon.geoms), polygon.area))

                    pylab.savefig('{rs}.png'.format(rs=rs))

                sql_start = time.time()
                self._insert_points(rs, points, 'start')
                sql_time = time.time() - sql_start

            num = increase_counter()
            self.logging.info('(%4d/%d) %s: Created %s points for "%s". Generation time: %s, SQL Time: %s',
                              num, self.total,
                              self.name, len(points), rec.name,
                              generation_time, sql_time)

    def _insert_points(self, rs, points, type):
        """Inserts generated Points into the database

        https://peterman.is/blog/postgresql-bulk-insertion/2013/08/

        :param rs:
        :param points:
        :param type:
        :return:
        """
        prepare_statement = 'PREPARE de_sim_points_plan (varchar, e_sim_point, geometry) AS ' \
                            'INSERT INTO de_sim_points (parent_geometry, point_type, geom) ' \
                            'VALUES($1, $2, ST_GeomFromWKB(ST_SetSRID($3, 900913)))'

        execute_statement = 'EXECUTE de_sim_points_plan({rs!r}, {type!r}, \'\\x{point!s}\'::bytea);'
        with connection.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(prepare_statement)

            # for p in points:
            # cur.execute('EXECUTE de_sim_points_plan (%s, %s, %s);', (rs, 'start', p.wkb))
            # Creating a list and mass execute it is faster :)

            sql_list = []
            for p in points:
                sql_list.append(execute_statement.format(rs=rs, point=p.wkb_hex, type='start'))

            cur.execute('\n'.join(sql_list))

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
        :param list u: List of N independent uniform values between 0 and 1
        :return: A list with point in the polygon
        :rtype: list
        """
        if n is 0:
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

            # k = bisect.bisect_left(u, p1.area / polygon.area)
            k = int(round(n * (p1.area / polygon.area)))

            return self._generate_points(p1, k) + self._generate_points(p2, n - k)
        else:
            v = []
            max_iterations = self.t * n + 5 * math.sqrt(self.t * n)
            v_length = len(v)
            while v_length < n and max_iterations > 0:
                max_iterations -= 1
                v.append(self._random_point_in_polygon(polygon))
                v_length = len(v)

            if len(v) < n:
                raise Exception('Too many interation')

            self.logging.debug('Generated %s points', n)

            return v

    def _random_point_in_polygon(self, polygon):
        """Returns random point in polygon

        :param Polygon poly:
        :return: A random point
        :rtype: Point
        """
        (minx, miny, maxx, maxy) = polygon.bounds
        while True:
            p = Point(npr.uniform(minx, maxx), npr.uniform(miny, maxy))
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

    def _get_total(self):
        sql = 'SELECT count(*) FROM {}'
        if self.kreise:
            sql = sql.format('de_commuter_kreise')
        else:
            sql = sql.format('de_commuter_gemeinden')

        with connection.get_connection() as con:
            cur = con.cursor()
            cur.execute(sql)
            self.total = cur.fetchone()[0]


def increase_counter():
    global counter
    with COUNTER_LOCK as lock:
        counter += 1
        result = counter
    return result


if __name__ == "__main__":
    import queue
    from shapely import speedups

    if speedups.available:
        speedups.enable()

    q = queue.Queue()
    q.put('06631')
    t = PointCreator('test', q)
    t.set_t(1.2)
    start = time.time()
    t.start()
    t.join()
    print(time.time() - start)


