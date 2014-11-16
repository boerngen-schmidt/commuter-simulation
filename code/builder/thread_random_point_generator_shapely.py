"""
Created on 29.09.2014

@author: Benjamin
"""
import threading
import math
import time
import logging

import numpy.random as npr
import pylab
from helper import database
from shapely.geometry import Polygon, Point
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
        :param Queue info_queue; Reference to the Queue with information
        :param bool kreise: True to create points within
        """
        threading.Thread.__init__(self)
        self.setName(name)
        self.queue = info_queue
        self.logging = logging.getLogger(name)
        self.kreise=kreise
        self.total=0

    def run(self):
        # sql = 'WITH area AS (SELECT c.*, s.geom FROM de_commuter_{tbl} c JOIN de_shp_{tbl} s ON c.rs = s.rs WHERE c.rs={rs}) '
        # sql += 'INSERT INTO de_sim_points (parent_geometry, point_type, geom) SELECT area.rs , \'{type}\', RandomPointsInPolygon(area.geom, (area.outgoing + area.within)) FROM area '
        sql = 'SELECT c.*, ST_AsEWKB(s.geom) AS geom_b FROM de_commuter_{tbl} c JOIN de_shp_{tbl} s ON c.rs = s.rs WHERE c.rs=\'{rs}\''

        if self.kreise:
            tbl='kreise'
        else:
            tbl='gemeinden'

        self.logging.info('Creating points for %s', tbl.upper())

        while not self.queue.empty():
            rs = self.queue.get()
            with database.get_connection() as con:
                cur = con.cursor(cursor_factory=NamedTupleCursor)
                cur.execute(sql.format(rs=rs, tbl=tbl))
                num = increase_counter()

                if cur.rowcount > 1:
                    self.logging.error('More than one geometry for "%s"', rs)
                else:
                    rec=cur.fetchone()
                    polygon = loads(bytes(rec.geom_b))
                    u = npr.uniform(0, 1, rec.outgoing)
                    u.sort()

                    points = self._generate_points(polygon, polygon.bounds, u)

                    pylab.figure(num=None, figsize=(20, 20), dpi=400)
                    for patch in polygon.geoms:
                        self._plot_polygon(patch)

                    # Plot the generated points
                    pylab.plot([p.x for p in points], [p.y for p in points], 'bs', alpha=0.75)

                    # Write the number of patches and the total patch area to the figure
                    pylab.text(-25, 25,
                        "Patches: %d, total area: %.2f" % (len(polygon.geoms), polygon.area))

                    pylab.savefig('fulda.png')
                    self.logging.debug('(%4d/%d) %s: Created points for "%s"', num, self.total, self.name, rec.name)

    def _plot_polygon(self, polygon):
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

    def _generate_points(self, polygon, bbox, u) -> list:
        """Generates sample points within a given geometry
            :param Polygon polygon: the polygon to create points in
            :param bbox: Bounding box for polygon
            :param list u: List of N independent uniform values between 0 and 1
            :return: A list with point in the polygon
            :rtype: list
            """
        n = len(u)
        self.logging.debug('Polygon Area: {}, N: {}'.format(*(polygon.area, n,)))
        if n is 0:
            return []
        area_polygon = polygon.area

        if area_polygon <= 0:
            return []
        t = 1.5
        bbox = polygon.bounds
        """(minx, miny, maxx, maxy) bbox"""
        if (area_polygon * t) < self._area_bbox(bbox):
            if (bbox[2] - bbox[0]) > (bbox[3] - bbox[1]):
                bbox_1 = self._bbox_left(bbox)
                bbox_2 = self._bbox_right(bbox)
            else:
                bbox_1 = self._bbox_bottom(bbox)
                bbox_2 = self._bbox_top(bbox)

            self.logging.info('Bounding box 1: minx:{0} miny:{1} maxx:{2} maxy:{3}'.format(*bbox_1))
            self.logging.info('Bounding box 2: minx:{0} miny:{1} maxx:{2} maxy:{3}'.format(*bbox_2))

            #TODO create real new polygons :(
            p1 = polygon
            p1 = p1.difference(Polygon(self._polygon_from_bbox(bbox_1)))
            pylab.figure(num=None, figsize=(20, 20), dpi=400)
            self._plot_polygon(p1)
            pylab.savefig('{n}_p1.png'.format(n=n))

            p2 = polygon
            p2 = p2.difference(Polygon(self._polygon_from_bbox(bbox_2)))
            pylab.figure(num=None, figsize=(20, 20), dpi=400)
            self._plot_polygon(p2)
            pylab.savefig('{n}_p2.png'.format(n=n))

            diff = p1.area / area_polygon
            self.logging.debug('Relation p1 to whole area: {} ({}/{}'.format(*(diff, p1.area, area_polygon)))

            # k = bisect.bisect_left(u, diff)
            k = math.floor(len(u)/diff)
            self.logging.info('Split index {k}; Number of points to generate {n}'.format(k=k, n=n))

            return self._generate_points(p1, bbox_1, u[:k]) + self._generate_points(p2, bbox_2, u[k + 1:])
        else:
            v = []
            max_iterations = t * n + 5 * math.sqrt(t * n)
            v_length = len(v)
            while v_length < n and max_iterations > 0:
                max_iterations -= 1
                v.append(self._random_point_in_polygon(polygon))
                v_length = len(v)

            if len(v) < n:
                raise Exception('Too many interation')

            self.logging.debug('Generated {} points'.format(len(v)))

            return v

    def _random_point_in_polygon(self, polygon):
        """Returns random point in polygon

        :param Polygon poly:
        :return: A random point
        :rtype: Point
        """
        (minx, miny, maxx, maxy) = polygon.bounds
        p = Point(minx-1, miny-1) #create an invalid start point
        while not polygon.contains(p):
            p = Point(npr.uniform(minx, maxx), npr.uniform(miny, maxy))
        return p

    def _area_bbox(self, bbox):
        """Calculates the area of a given bounding box

        :param tuple bbox: (minx, miny, maxx, maxy) tuple
        :return: Area of bounding box
        :rtype: float
        """
        return (bbox[2]-bbox[0]) * (bbox[3]-bbox[1])

    def _polygon_from_bbox(self, bbox):
        return Polygon([(bbox[0], bbox[1]), (bbox[0], bbox[3]), (bbox[2], bbox[3]), (bbox[2], bbox[1])])

    def _bbox_left(self, bbox):
        """Returns left half of bbox"""
        l=(bbox[2]-bbox[0]) / 2
        return bbox[0], bbox[1], bbox[2]-l, bbox[3]

    def _bbox_right(self, bbox):
        """Returns right half of bbox"""
        l=(bbox[2]-bbox[0]) / 2
        return bbox[0]+l, bbox[1], bbox[2], bbox[3]

    def _bbox_top(self, bbox):
        """Returns top half of bbox"""
        l=(bbox[3]-bbox[1]) / 2
        return bbox[0], bbox[1]+l, bbox[2], bbox[3]

    def _bbox_bottom(self, bbox):
        """Returns bottom half of bbox"""
        l=(bbox[3]-bbox[1]) / 2
        return bbox[0], bbox[1], bbox[2], bbox[3]-l

    def do_kreise(self):
        while not self.queue.empty():
            rs = self.queue.get()
            with database.get_connection() as con:
                cur = con.cursor()
                sql = 'WITH area AS (SELECT c.*, s.geom FROM de_commuter_gemeinden c JOIN de_shp_gemeinden s ON c.rs = s.rs WHERE c.rs=%s) '
                sql += 'INSERT INTO de_sim_points (parent_geometry, point_type, geom) SELECT area.rs , \'start\', RandomPointsInPolygon(area.geom, (area.outgoing + area.within)) FROM area '
                cur.execute(sql, (rs,))
                num = increase_counter()

                cur.execute('SELECT gen FROM de_shp_gemeinden WHERE rs = %s', (rs,))
                logger.debug('(%4d/%d) %s: Created points for Gemeinde "%s"', num, self.total, self.name, cur.fetchone()[0])

    def _get_total(self):
        sql = 'SELECT count(*) FROM {1}'
        if self.kreise:
            sql.format('de_commuter_kreise')
        else:
            sql.format('de_commuter_gemeinden')

        with database.get_connection() as con:
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
    from helper import logger

    q=queue.Queue()
    q.put('06631')
    t=PointCreator('test', q)
    start=time.time()
    t.start()
    t.join()
    print(time.time()-start)


