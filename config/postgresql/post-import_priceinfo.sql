-- Table: priceinfo
BEGIN;
DROP TABLE IF EXISTS de_tt_priceinfo;

CREATE TABLE de_tt_priceinfo
(
  id integer NOT NULL DEFAULT nextval('priceinfo_id_seq'::regclass),
  station_id varchar(60),
  recieved timestamptz NOT NULL DEFAULT now(),
  e5 numeric(4,3),
  e10 numeric(4,3),
  diesel numeric(4,3),
  CONSTRAINT de_tt_priceinfo_id_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);

INSERT INTO de_tt_priceinfo (SELECT id, station_id, recieved::timestamptz AT TIME ZONE 'Europe/Berlin', e5, e10, diesel from priceinfo);

-- Set the start price to the first known price
INSERT INTO de_tt_priceinfo (station_id, recieved, e5, e10, diesel)
SELECT t1.station_id as station_id, '2014-06-01 00:00:01+2'::timestamptz as recieved, e5, e10, diesel
FROM de_tt_priceinfo t1
INNER JOIN
(
  SELECT min(recieved) minval, station_id
  FROM de_tt_priceinfo
  GROUP BY station_id
) t2
ON t1.recieved = t2.minval AND t1.station_id = t2.station_id;

CREATE INDEX de_tt_priceinfo_recieved_station_id_idx
  ON public.de_tt_priceinfo
  USING btree
  (recieved, station_id COLLATE pg_catalog."default");

CREATE INDEX index_station_id
   ON de_tt_priceinfo (station_id ASC NULLS LAST);

-- Drop old table
DROP TABLE priceinfo;
COMMIT;