BEGIN;
    DROP TABLE IF EXISTS de_sim_points_lookup;
    CREATE TABLE de_sim_points_lookup
    (
      id serial NOT NULL,
      rs character varying(12),
      point_type character varying(15),
      geom geometry(Point,4326),
      CONSTRAINT de_sim_points_lookup_pkey PRIMARY KEY (id)
    );

    DROP TABLE IF EXISTS de_sim_points CASCADE;
    CREATE TABLE de_sim_points
    (
      id serial NOT NULL,
      rs character varying(12),
      used boolean DEFAULT false,
      lookup integer,
      geom geometry(Point,4326),
      CONSTRAINT de_sim_points_pkey PRIMARY KEY (id)
    );

    CREATE TABLE de_sim_points_start (
        CONSTRAINT de_sim_points_start_pkey PRIMARY KEY (id)
    ) INHERITS (de_sim_points);

    CREATE TABLE de_sim_points_within_start (
        CONSTRAINT de_sim_points_within_start_pkey PRIMARY KEY (id)
    ) INHERITS (de_sim_points);

    CREATE TABLE de_sim_points_end (
        CONSTRAINT de_sim_points_end_pkey PRIMARY KEY (id)
    ) INHERITS (de_sim_points);

    CREATE TABLE de_sim_points_within_end (
        CONSTRAINT de_sim_points_within_end_pkey PRIMARY KEY (id)
    ) INHERITS (de_sim_points);
COMMIT;