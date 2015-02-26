-- Table: stations
BEGIN;
    DROP TABLE IF EXISTS de_tt_stations CASCADE;

    CREATE TABLE de_tt_stations
    (
      id character varying(38) NOT NULL,
      "name" character varying(255),
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
      geom geometry(Point,25832),
      CONSTRAINT de_tt_stations_id_pkey PRIMARY KEY (id)
    );
    ALTER TABLE stations OWNER TO benjamin;

    -- Populate Table
    INSERT INTO de_tt_stations (
      id, name, brand, street, "number", zip, city,
      premium_e5_time, premium_e5_value, premium_e10_time, premium_e10_value, diesel_time, diesel_value,
      holiday_identifier, opening_times, opening_times_extended, override_opening_times,
      geom)
      SELECT id, name, brand, street, "number", zip, city,
      premium_e5_time, premium_e5_value, premium_e10_time, premium_e10_value, diesel_time, diesel_value,
      holiday_identifier, opening_times, opening_times_extended, override_opening_times,
      ST_Transform(ST_SetSRID(ST_POINT(longitude, latitude), 4326), 25832) AS geom
      FROM stations;

    CREATE INDEX de_tt_stations_geom_index ON public.de_tt_stations USING gist (geom) WITH (FILLFACTOR=100);
    -- DROP old table
    DROP TABLE stations;
COMMIT;

-- Table: priceinfo
BEGIN;
    DROP TABLE IF EXISTS de_tt_priceinfo;

    CREATE TABLE de_tt_priceinfo
    (
      id serial,
      station_id varchar(38),
      received timestamptz NOT NULL DEFAULT now(),
      e5 numeric(4,3),
      e10 numeric(4,3),
      diesel numeric(4,3),
      CONSTRAINT de_tt_priceinfo_id_pkey PRIMARY KEY (id)
    )
    WITH (
      OIDS=FALSE
    );

    INSERT INTO de_tt_priceinfo (SELECT id, station_id, recieved::timestamptz AT TIME ZONE 'Europe/Berlin' as received, e5, e10, diesel from priceinfo);

    CREATE INDEX de_tt_priceinfo_received_station_id_idx ON public.de_tt_priceinfo USING btree (received, station_id COLLATE pg_catalog."default");

    -- Index for best serach speed for prices
    CREATE INDEX de_tt_priceinfo_station_id_received_idx ON public.de_tt_priceinfo (station_id ASC NULLS LAST, received ASC NULLS LAST);

    -- Set the start price to the first known price
    INSERT INTO de_tt_priceinfo (station_id, received, e5, e10, diesel)
    SELECT station_id, '2014-06-01 00:00:01+2'::timestamptz as received, e5, e10, diesel
    FROM  (SELECT min(received) minval, station_id FROM de_tt_priceinfo GROUP BY station_id) s
    LEFT JOIN LATERAL (
        SELECT e5, e10, diesel, received
        FROM   de_tt_priceinfo
        WHERE  station_id = s.station_id
        AND    received = s.minval
        ORDER  BY received DESC
        LIMIT  1
       )  p ON TRUE;

    -- Drop old table
    DROP TABLE priceinfo;
COMMIT;