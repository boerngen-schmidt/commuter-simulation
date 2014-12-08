DROP TABLE IF EXISTS de_sim_points CASCADE;

CREATE TABLE de_sim_points
(
  id serial NOT NULL,
  parent_geometry character varying(12),
  used boolean DEFAULT false,
  CONSTRAINT de_sim_points_pkey PRIMARY KEY (id)
);

SELECT AddGeometryColumn('de_sim_points', 'geom', 900913, 'POINT', 2);

CREATE TABLE de_sim_points_start
(
  CONSTRAINT de_sim_points_start_pkey PRIMARY KEY (id)
)
INHERITS (de_sim_points)
WITH (
  OIDS=FALSE
);

CREATE TABLE de_sim_points_within_start
(
  CONSTRAINT de_sim_points_within_start_pkey PRIMARY KEY (id)
)
INHERITS (de_sim_points)
WITH (
  OIDS=FALSE
);

CREATE TABLE de_sim_points_end
(
  CONSTRAINT de_sim_points_end_pkey PRIMARY KEY (id)
)
INHERITS (de_sim_points)
WITH (
  OIDS=FALSE
);

CREATE TABLE de_sim_points_within_end
(
  CONSTRAINT de_sim_points_within_end_pkey PRIMARY KEY (id)
)
INHERITS (de_sim_points)
WITH (
  OIDS=FALSE
);

-- DO language plpgsql $$
--   DECLARE
--     i int8;
--     total int8;
--     area record;
--   BEGIN
--     i := 1;
--     SELECT count(*) INTO total FROM de_commuter_kreise;
--
--     RAISE NOTICE 'Starting to create Points for % kreise  ...', total;
--     FOR area IN SELECT c.*, s.gen, s.geom from de_commuter_kreise c join de_shp_kreise s on c.rs = s.rs LOOP
--       RAISE NOTICE '   Kreis "%" (% / %)', area.gen, i, total;
--       INSERT INTO de_sim_points (parent_geometry, point_type, geom) SELECT area.rs , 'start', randompointsinpolygon(area.geom, (area.outgoing + area.within));
--       i := i + 1;
--     END LOOP;
--   END;
-- $$;
--
-- DO language plpgsql $$
--   DECLARE
--     i int8;
--     total int8;
--     area record;
--   BEGIN
--     i := 1;
--     SELECT count(*) INTO total FROM de_commuter_gemeinden;
--
--     RAISE NOTICE 'Starting to create Points for % kreise  ...', total;
--     FOR area IN SELECT c.*, s.gen, s.geom from de_commuter_gemeinden c join de_shp_gemeinden s on c.rs = s.rs LOOP
--       RAISE NOTICE '   Gemeinde "%" (% / %)', area.gen, i, total;
--       INSERT INTO de_sim_points (parent_geometry, point_type, geom) SELECT area.rs , 'start', randompointsinpolygon(area.geom, (area.outgoing + area.within));
--       i := i + 1;
--     END LOOP;
--   END;
-- $$;