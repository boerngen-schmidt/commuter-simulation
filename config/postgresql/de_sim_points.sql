BEGIN;
DROP TABLE IF EXISTS de_sim_points_lookup;
CREATE TABLE de_sim_points_lookup
(
  id serial NOT NULL,
  rs character varying(12),
  type character varying(15),
  CONSTRAINT de_sim_points_lookup_pkey PRIMARY KEY (id)
);
SELECT AddGeometryColumn('de_sim_points_lookup', 'geom_meter', 900913, 'POINT', 2);

DROP TABLE IF EXISTS de_sim_points CASCADE;

CREATE TABLE de_sim_points
(
  id serial NOT NULL,
  parent_geometry character varying(12),
  used boolean DEFAULT false,
  lookup integer,
  CONSTRAINT de_sim_points_pkey PRIMARY KEY (id)
);

SELECT AddGeometryColumn('de_sim_points', 'geom', 4326, 'POINT', 2);
SELECT AddGeometryColumn('de_sim_points', 'geom_meter', 900913, 'POINT', 2);

CREATE TABLE de_sim_points_start
(
  CONSTRAINT de_sim_points_start_pkey PRIMARY KEY (id)
)
INHERITS (de_sim_points)
WITH (
  OIDS=FALSE
);

CREATE TABLE de_sim_points_within_start
(
  CONSTRAINT de_sim_points_within_start_pkey PRIMARY KEY (id)
)
INHERITS (de_sim_points)
WITH (
  OIDS=FALSE
);

CREATE TABLE de_sim_points_end
(
  CONSTRAINT de_sim_points_end_pkey PRIMARY KEY (id)
)
INHERITS (de_sim_points)
WITH (
  OIDS=FALSE
);

CREATE TABLE de_sim_points_within_end
(
  CONSTRAINT de_sim_points_within_end_pkey PRIMARY KEY (id)
)
INHERITS (de_sim_points)
WITH (
  OIDS=FALSE
);
COMMIT;