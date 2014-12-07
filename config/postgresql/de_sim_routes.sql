-- Table: de_sim_routes

DROP TABLE IF EXISTS de_sim_routes CASCADE;

CREATE TABLE de_sim_routes
(
  id serial NOT NULL,
  start_point serial NOT NULL,
  end_point serial NOT NULL
)
WITH (
  OIDS=FALSE
);

CREATE TABLE de_sim_routes_within
(
  CONSTRAINT de_sim_routes_within_pkey PRIMARY KEY (id),
  CONSTRAINT de_sim_routes_end_point_fkey FOREIGN KEY (end_point)
      REFERENCES de_sim_points_within_end (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE CASCADE,
  CONSTRAINT de_sim_routes_start_point_fkey FOREIGN KEY (start_point)
      REFERENCES de_sim_points_within_start (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE CASCADE
)
INHERITS (de_sim_routes)
WITH (
  OIDS=FALSE
);

CREATE TABLE de_sim_routes_outgoing
(
  CONSTRAINT de_sim_routes_outgoing_pkey PRIMARY KEY (id),
  CONSTRAINT de_sim_routes_end_point_fkey FOREIGN KEY (end_point)
      REFERENCES de_sim_points_end (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE CASCADE,
  CONSTRAINT de_sim_routes_start_point_fkey FOREIGN KEY (start_point)
      REFERENCES de_sim_points_start (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE CASCADE
)
INHERITS (de_sim_routes)
WITH (
  OIDS=FALSE
);