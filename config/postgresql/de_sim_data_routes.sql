-- Table: public.de_sim_data_routes

DROP TABLE IF EXISTS de_sim_data_routes;

CREATE TABLE de_sim_data_routes
(
  c_id integer NOT NULL,
  seq integer NOT NULL,
  source integer,
  destination integer,
  clazz integer,
  kmh integer,
  work boolean NOT NULL,
  CONSTRAINT de_sim_data_routes_pkey PRIMARY KEY (c_id, seq, work)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE public.de_sim_data_routes
  OWNER TO benjamin;