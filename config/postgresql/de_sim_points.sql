CREATE TYPE e_sim_point AS ENUM ('start', 'end');

DROP TABLE IF EXISTS de_sim_points;
CREATE TABLE de_sim_points
(
  id serial PRIMARY KEY,
  parent_geometry varchar(12) REFERENCES de_shp (rs),
  point_type e_sim_point
);

SELECT AddGeometryColumn('de_sim_points', 'geom', 900913, 'POINT', 2);