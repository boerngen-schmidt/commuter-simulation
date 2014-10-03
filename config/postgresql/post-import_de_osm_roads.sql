DROP INDEX IF EXISTS de_osm_roads_highway_index;

﻿CREATE INDEX de_osm_roads_highway_index
   ON de_osm_roads (highway ASC NULLS LAST);