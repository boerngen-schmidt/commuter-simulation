BEGIN;
    DROP INDEX IF EXISTS de_osm_polygon_landuse_way_idx;
    CREATE INDEX de_osm_polygon_landuse_way_idx ON de_osm_polygon USING gist (landuse COLLATE pg_catalog."default", way);
COMMIT;