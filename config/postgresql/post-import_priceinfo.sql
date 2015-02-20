-- Table: priceinfo
BEGIN;
DROP TABLE IF EXISTS de_tt_priceinfo;

CREATE TABLE de_tt_priceinfo
(
  id integer NOT NULL DEFAULT nextval('priceinfo_id_seq'::regclass),
  station_id varchar(60),
  received timestamptz NOT NULL DEFAULT now(),
  e5 numeric(4,3),
  e10 numeric(4,3),
  diesel numeric(4,3),
  CONSTRAINT de_tt_priceinfo_id_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);

INSERT INTO de_tt_priceinfo (SELECT id, station_id, received::timestamptz AT TIME ZONE 'Europe/Berlin', e5, e10, diesel from priceinfo);

CREATE INDEX de_tt_priceinfo_received_station_id_idx
  ON public.de_tt_priceinfo
  USING btree
  (received, station_id COLLATE pg_catalog."default");

-- Index for best serach speed for prices
CREATE INDEX de_tt_priceinfo_station_id_received_idx
  ON public.de_tt_priceinfo (station_id ASC NULLS LAST, received ASC NULLS LAST);

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