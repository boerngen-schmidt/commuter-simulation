BEGIN;
CREATE TYPE e_sim_point AS ENUM ('start', 'end');
END;

DROP TABLE IF EXISTS de_sim_points;
CREATE TABLE de_sim_points
(
  id serial PRIMARY KEY,
  parent_geometry varchar(12),
  point_type e_sim_point
);

SELECT AddGeometryColumn('de_sim_points', 'geom', 900913, 'POINT', 2);