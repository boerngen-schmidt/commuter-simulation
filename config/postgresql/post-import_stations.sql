-- Table: stations

DROP TABLE IF EXISTS de_tt_stations CASCADE;

CREATE TABLE de_tt_stations
(
  id character varying(255) NOT NULL,
  name character varying(255),
  brand character varying(255),
  street character varying(255),
  "number" character varying(255),
  zip character varying(255),
  city character varying(255),
  premium_e5_time timestamp without time zone,
  premium_e5_value double precision,
  premium_e10_time timestamp without time zone,
  premium_e10_value double precision,
  diesel_time timestamp without time zone,
  diesel_value double precision,
  holiday_identifier character varying(255),
  opening_times text,
  opening_times_extended text,
  override_opening_times text,
  geom geometry(Point,4326),
  CONSTRAINT de_tt_stations_id_pkey PRIMARY KEY (id)
);
ALTER TABLE stations OWNER TO benjamin;
CREATE INDEX de_tt_stations_geom_index ON public.de_tt_stations USING gist (geom) WITH (FILLFACTOR=100);

-- Populate Table
INSERT INTO de_tt_stations (
  id, name, brand, street, "number", zip, city, 
  premium_e5_time, premium_e5_value, premium_e10_time, premium_e10_value, diesel_time, diesel_value, 
  holiday_identifier, opening_times, opening_times_extended, override_opening_times,
  geom)
  SELECT id, name, brand, street, "number", zip, city, 
  premium_e5_time, premium_e5_value, premium_e10_time, premium_e10_value, diesel_time, diesel_value, 
  holiday_identifier, opening_times, opening_times_extended, override_opening_times,
  ST_SetSRID(ST_POINT(longitude, latitude), 4326) AS geom
  FROM stations;
  
-- DROP old table
DROP TABLE stations;  
