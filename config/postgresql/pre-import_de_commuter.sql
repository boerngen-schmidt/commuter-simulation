-- Table: de_commuter

DROP TABLE IF EXISTS de_commuter CASCADE;

--- Create table for commuters 
CREATE TABLE de_commuter
(
  ags character(12) NOT NULL,
  name text,
  within integer,
  home integer,
  incoming integer,
  outgoing integer,
  CONSTRAINT de_commuter_pkey PRIMARY KEY (ags)
)
WITH (OIDS=FALSE);

SELECT AddGeometryColumn('de_commuter', 'geom', 900913, 'POLYGON', 2);
  
-- Table: de_commuter_kreise

DROP TABLE IF EXISTS de_commuter_kreise;

CREATE TABLE de_commuter_kreise
(
-- Geerbt from table de_commuter:  ags character(12) NOT NULL,
-- Geerbt from table de_commuter:  within integer,
-- Geerbt from table de_commuter:  home integer,
-- Geerbt from table de_commuter:  outgoing integer,
-- Geerbt from table de_commuter:  incoming integer,
-- Geerbt from table de_commuter:  geom geometry(Polygon,900913)
)
INHERITS (de_commuter)
WITH (
  OIDS=FALSE
);

-- Table: de_commuter_kreise

DROP TABLE IF EXISTS de_commuter_gemeinden;

CREATE TABLE de_commuter_gemeinden
(
-- Geerbt from table de_commuter:  ags character(12) NOT NULL,
-- Geerbt from table de_commuter:  within integer,
-- Geerbt from table de_commuter:  home integer,
-- Geerbt from table de_commuter:  outgoing integer,
-- Geerbt from table de_commuter:  incoming integer,
-- Geerbt from table de_commuter:  geom geometry(Polygon,900913)
)
INHERITS (de_commuter)
WITH (
  OIDS=FALSE
);

