BEGIN;
    DROP TABLE IF EXISTS de_sim_data_commuter;
    CREATE TABLE de_sim_data_commuter
    (
        c_id INT NOT NULL,
        leaving_time INTERVAL NOT NULL,
        route_home_distance DOUBLE PRECISION NOT NULL,
        route_work_distance DOUBLE PRECISION NOT NULL,
        fuel_type VARCHAR(6),
        tank_filling DOUBLE PRECISION,
        error VARCHAR(32)
    );
    CREATE INDEX de_sim_data_commuter_c_id_idx ON de_sim_data_commuter (c_id);

    DROP TABLE IF EXISTS de_sim_data_refill;
    CREATE TABLE de_sim_data_refill
    (
        id SERIAL PRIMARY KEY NOT NULL,
        c_id INT,
        rerun BOOL,
        amount DOUBLE PRECISION,
        price DOUBLE PRECISION,
        refueling_time TIMESTAMP,
        station VARCHAR(38),
        fuel_type VARCHAR(6)
    );
    CREATE INDEX de_sim_data_refill_c_id_rerun_idx ON de_sim_data_refill (c_id, rerun);

    DROP TABLE IF EXISTS de_sim_data_routes;
    CREATE TABLE de_sim_data_routes
    (
      c_id integer NOT NULL,
      clazz integer,
      km double precision,
      avg_kmh integer,
      work_route boolean NOT NULL,
      CONSTRAINT de_sim_data_routes_pkey PRIMARY KEY (c_id, work)
    );

    DROP TABLE IF EXISTS de_sim_data_matching_info;
    CREATE TABLE public.de_sim_data_matching_info
    (
      rs character varying(12) NOT NULL,
      max_d integer NOT NULL,
      min_d integer NOT NULL,
      done integer,
      total integer,
      CONSTRAINT de_sim_matching_info_pkey PRIMARY KEY (rs, max_d, min_d)
    );
COMMIT;