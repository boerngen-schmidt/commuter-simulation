DROP INDEX IF EXISTS de_osm_polygon_gemeindeschluessel;

CREATE INDEX de_osm_polygon_gemeindeschluessel
  ON de_osm_polygon
  USING btree
  ("de:amtlicher_gemeindeschluessel");

DROP INDEX IF EXISTS de_osm_polygon_admin_level;

CREATE INDEX de_osm_polygon_admin_level
  ON de_osm_polygon
  USING btree
  (admin_level);