-- Table: priceinfo

DROP TABLE IF EXISTS de_tt_priceinfo;

CREATE TABLE de_tt_priceinfo
(
  id integer NOT NULL DEFAULT nextval('priceinfo_id_seq'::regclass),
  station_id varchar(60) REFERENCES de_tt_stations (id),
  received timestamptz NOT NULL DEFAULT now(),
  e5 numeric(4,3),
  e10 numeric(4,3),
  diesel numeric(4,3),
  CONSTRAINT de_tt_priceinfo_id_pkey PRIMARY KEY (id)
)
WITH (
  OIDS=FALSE
);
ALTER TABLE priceinfo
  OWNER TO benjamin;

CREATE INDEX index_station_id
   ON de_tt_priceinfo (station_id ASC NULLS LAST);

INSERT INTO de_tt_priceinfo (SELECT id, station_id, received::timestamptz AT TIME ZONE 'Europe/Berlin', e5, e10, diesel from priceinfo);


-- Drop old table
DROP TABLE priceinfo;