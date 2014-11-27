-- Table: de_sim_routes

-- DROP TABLE de_sim_routes;

CREATE TABLE de_sim_routes
(
  id serial NOT NULL,
  start_point serial NOT NULL,
  end_point serial NOT NULL,
  CONSTRAINT de_sim_routes_pkey PRIMARY KEY (id),
  CONSTRAINT de_sim_routes_end_point_fkey FOREIGN KEY (end_point)
      REFERENCES de_sim_points (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE CASCADE,
  CONSTRAINT de_sim_routes_start_point_fkey FOREIGN KEY (start_point)
      REFERENCES de_sim_points (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE CASCADE
)
WITH (
  OIDS=FALSE
);
ALTER TABLE de_sim_routes
  OWNER TO benjamin;