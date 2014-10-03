'''
Created on 11.09.2014

@author: benjamin
'''
import psycopg2
conn = psycopg2.connect(database='spritsim', user='benjamin', password='therock', host='localhost')
cur = conn.cursor()

cur.execute('SELECT id, osm_id, osm_name, osm_meta, osm_source_id, osm_target_id, clazz, flags, source, target, '+
            'km, kmh, cost, reverse_cost, x1, y1, x2, y2, st_astext(geom_way) '+
            'FROM de_2po_4pgr '+
            'WHERE osm_name =\'Bleichstraße\'')
fetch = cur.fetchone()
print(fetch)


cur.close()
conn.close()