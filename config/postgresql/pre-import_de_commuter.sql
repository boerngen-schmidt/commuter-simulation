--- Create table for commuters 
CREATE TABLE de_commuter
(
  ags varchar(12),
  bundesland int2,
  regierungsbezirk int2,
  kreis int2,
  verband int2,
  gemeinde int2,
  name text,
  within integer,
  home integer,
  outgoing integer,
  incoming integer,
  CONSTRAINT PRIMARY KEY de_commuter_pk(ags),
)
WITH (OIDS=FALSE);

SELECT AddGeometryColumn('de_commuter', 'geom', 900913, 'POLYGON', 2);
  
CREATE TABLE de_commuter_kreise()
WITH (OIDS=FALSE)
INHERITS (de_commuter);

CREATE TABLE de_commuter_gemeinden()
WITH (OIDS=FALSE)
INHERITS (de_commuter);

CREATE TABLE de_commuter_other()
WITH (OIDS=FALSE)
INHERITS (de_commuter);

CREATE OR REPLACE FUNCTION #spritsim'.trigger_insert_de_commuter()
    RETURNS trigger AS
$$
DECLARE
    var_ags text;
BEGIN
    IF NEW.ags