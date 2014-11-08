-- Table: de_commuter

DROP TABLE IF EXISTS de_commuter CASCADE;

--- Create table for commuters 
CREATE TABLE de_commuter
(
  rs character varying(12) NOT NULL,
  name text,
  within integer,
  home integer,
  incoming integer,
  outgoing integer,
  CONSTRAINT de_commuter_pkey PRIMARY KEY (rs)
)
WITH (
  OIDS=FALSE
);
  
-- Table: de_commuter_kreise

DROP TABLE IF EXISTS de_commuter_kreise;

CREATE TABLE de_commuter_kreise
(
-- Geerbt from table de_commuter:  rs character varying(12) NOT NULL,
-- Geerbt from table de_commuter:  within integer,
-- Geerbt from table de_commuter:  home integer,
-- Geerbt from table de_commuter:  outgoing integer,
-- Geerbt from table de_commuter:  incoming integer,
  CONSTRAINT de_communter_kreise_pkey PRIMARY KEY (rs)
)
INHERITS (de_commuter)
WITH (
  OIDS=FALSE
);

-- Table: de_commuter_kreise

DROP TABLE IF EXISTS de_commuter_gemeinden;

CREATE TABLE de_commuter_gemeinden
(
-- Geerbt from table de_commuter:  rs character varying(12) NOT NULL,
-- Geerbt from table de_commuter:  within integer,
-- Geerbt from table de_commuter:  home integer,
-- Geerbt from table de_commuter:  outgoing integer,
-- Geerbt from table de_commuter:  incoming integer,
  CONSTRAINT de_communter_gemeinden_pkey PRIMARY KEY (rs)
)
INHERITS (de_commuter)
WITH (
  OIDS=FALSE
);

