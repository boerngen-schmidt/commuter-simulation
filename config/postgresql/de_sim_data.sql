BEGIN;
    DROP TABLE IF EXISTS de_sim_data_commuter;
    CREATE TABLE de_sim_data_commuter
    (
        c_id INT NOT NULL,
        leaving_time TIME NOT NULL,
        route_home_distance DOUBLE PRECISION NOT NULL,
        route_work_distance DOUBLE PRECISION NOT NULL,
        error VARCHAR(32)
    );
    CREATE INDEX de_sim_data_commuter_c_id_idx ON de_sim_data_commuter (c_id);

    DROP TABLE IF EXISTS de_sim_data_refill;
    CREATE TABLE de_sim_data_refill
    (
        id SERIAL PRIMARY KEY NOT NULL,
        c_id INT,
        amount DOUBLE PRECISION,
        price DOUBLE PRECISION,
        refueling_time TIMESTAMP,
        station VARCHAR(38),
        fuel_type VARCHAR(10)
    );
    CREATE INDEX de_sim_data_refill_c_id_idx ON de_sim_data_refill (c_id);

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
    );
COMMIT;