BEGIN;
    DROP TABLE IF EXISTS de_sim_routes CASCADE;
    CREATE TABLE de_sim_routes
    (
      id serial NOT NULL,
      start_point int NOT NULL,
      end_point int NOT NULL,
      distance_meter double precision
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
    ) INHERITS (de_sim_routes);
    CREATE INDEX ON de_sim_routes_within USING btree (start_point);

    CREATE TABLE de_sim_routes_outgoing
    (
      CONSTRAINT de_sim_routes_outgoing_pkey PRIMARY KEY (id),
      CONSTRAINT de_sim_routes_end_point_fkey FOREIGN KEY (end_point)
          REFERENCES de_sim_points_end (id) MATCH SIMPLE
          ON UPDATE NO ACTION ON DELETE CASCADE,
      CONSTRAINT de_sim_routes_start_point_fkey FOREIGN KEY (start_point)
          REFERENCES de_sim_points_start (id) MATCH SIMPLE
          ON UPDATE NO ACTION ON DELETE CASCADE
    ) INHERITS (de_sim_routes);
    CREATE INDEX ON de_sim_routes_outgoing (start_point ASC NULLS LAST, distance_meter ASC NULLS LAST);

    CREATE TABLE de_sim_routes_outgoing_sampled
    (
      commuter integer NOT NULL,
      CONSTRAINT de_sim_routes_outgoing_sampled_pkey PRIMARY KEY (commuter),
      CONSTRAINT de_sim_routes_outgoing_sampled_commuter_fkey FOREIGN KEY (commuter)
          REFERENCES public.de_sim_routes_outgoing (id) MATCH SIMPLE
          ON UPDATE NO ACTION ON DELETE CASCADE
    );

    CREATE TABLE de_sim_routes_within_sampled
    (
      commuter integer NOT NULL,
      CONSTRAINT de_sim_routes_within_sampled_pkey PRIMARY KEY (commuter),
      CONSTRAINT de_sim_routes_within_sampled_commuter_fkey FOREIGN KEY (commuter)
          REFERENCES de_sim_routes_within (id) MATCH SIMPLE
          ON UPDATE NO ACTION ON DELETE CASCADE
    );
COMMIT;

