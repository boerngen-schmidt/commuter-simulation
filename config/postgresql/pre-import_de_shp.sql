/*
 * Table: de_shp
 */
DROP TABLE IF EXISTS de_shp CASCADE;
CREATE TABLE de_shp
(
  gid serial NOT NULL,
  objectid integer,
  use numeric,
  rs character varying(12),
  gf numeric,
  rau_rs character varying(12),
  gen character varying(50),
  des character varying(75),
  ags character varying(12),
  rs_alt character varying(20),
  wirksamkei timestamp with time zone,
  debkg_id character varying(16),
  length numeric,
  shape_leng numeric,
  shape_area numeric,
  geom geometry(MultiPolygon,900913),
  CONSTRAINT de_shp_pkey PRIMARY KEY (gid)
)
WITH (
  OIDS=FALSE
);

/*
﻿ * Table: de_shp_bundeslaender
 */
DROP TABLE IF EXISTS de_shp_bundeslaender;
CREATE TABLE de_shp_bundeslaender
(
  CONSTRAINT de_shp_bundeslaender_pkey PRIMARY KEY (gid)
)
INHERITS (de_shp)
WITH (
  OIDS=FALSE
);

-- Index: de_shp_rs_index
DROP INDEX IF EXISTS de_shp_bundeslaender_rs_index;
CREATE INDEX de_shp_bundeslaender_rs_index
  ON de_shp_bundeslaender
  USING btree
  (rs COLLATE pg_catalog."default");

/*
﻿ * Table: de_shp_kreise
 */
DROP TABLE IF EXISTS de_shp_kreise;
CREATE TABLE de_shp_kreise
(
  CONSTRAINT de_shp_kreise_pkey PRIMARY KEY (gid)
)
INHERITS (de_shp)
WITH (
  OIDS=FALSE
);

-- Index: de_shp_kreise_rs_index
DROP INDEX IF EXISTS de_shp_kreise_rs_index;
CREATE INDEX de_shp_kreise_rs_index
  ON de_shp_kreise
  USING btree
  (rs COLLATE pg_catalog."default");

/*
﻿ * Table: de_shp_gemeinden
 */
DROP TABLE IF EXISTS de_shp_gemeinden;
CREATE TABLE de_shp_gemeinden
(
  CONSTRAINT de_shp_gemeinden_pkey PRIMARY KEY (gid)
)
INHERITS (de_shp)
WITH (
  OIDS=FALSE
);

-- Index: de_shp_gemeinden_rs_index
DROP INDEX IF EXISTS de_shp_gemeinden_rs_index;
CREATE INDEX de_shp_gemeinden_rs_index
  ON de_shp_gemeinden
  USING btree
  (rs COLLATE pg_catalog."default");

/*
﻿ * Table: de_shp_verwaltungsgemeinschaften
 */
DROP TABLE IF EXISTS de_shp_verwaltungsgemeinschaften;
CREATE TABLE de_shp_verwaltungsgemeinschaften
(
  CONSTRAINT de_shp_verwaltungsgemeinschaften_pkey PRIMARY KEY (gid)
)
INHERITS (de_shp)
WITH (
  OIDS=FALSE
);

-- Index: de_shp_verwaltungsgemeinschaften_rs_index
DROP INDEX IF EXISTS de_shp_verwaltungsgemeinschaften_rs_index;
CREATE INDEX de_shp_verwaltungsgemeinschaften_rs_index
  ON de_shp_verwaltungsgemeinschaften
  USING btree
  (rs COLLATE pg_catalog."default");