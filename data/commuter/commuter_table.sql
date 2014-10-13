--- Create table for commuters 
CREATE TABLE de_commuter
(
  ags text,
  name text,
  within integer,
  home integer,
  outgoing integer,
  incoming integer
)
WITH (OIDS=FALSE);
  
CREATE TABLE de_commuter_kreise()
WITH (OIDS=FALSE)
INHERITS (cities);

CREATE TABLE de_commuter_gemeinden()
WITH (OIDS=FALSE)
INHERITS (cities);