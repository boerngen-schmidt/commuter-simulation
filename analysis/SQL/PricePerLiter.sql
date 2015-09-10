WITH
	bab_stations AS(
		SELECT id 
		FROM de_tt_stations_modified 
		WHERE LOWER(street) ~  '(a\\d+|a\\s+\\d+|bab|autohof|rasthof|autobahn|^a$)' OR LOWER(name) ~ 'bat'
	),
	brands AS(
		SELECT brand, count(brand) 
		FROM de_tt_stations_modified 
		WHERE LOWER(brand) NOT IN ('bft', 'freie tankstelle')
		GROUP BY brand 
		HAVING COUNT(brand) > 200
	)
SELECT
	r.c_id,
	refueling_time,
	CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 1
		THEN 1
		ELSE 0
	END as mon,
	CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 2
		THEN 1
		ELSE 0
	END as tue,
	CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 3
		THEN 1
		ELSE 0
	END as wed,
	CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 4
		THEN 1
		ELSE 0
	END as thu,
	CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 5
		THEN 1
		ELSE 0
	END as fri,
	CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 6
	THEN 1
	ELSE 0
	END as sat,
	CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 7
		THEN 1
		ELSE 0
	END as sun,
	CASE WHEN EXTRACT(HOUR FROM r.refueling_time) BETWEEN 4 AND 10
		THEN 1
		ELSE 0
	END as morning,
	CASE WHEN EXTRACT(HOUR FROM r.refueling_time) BETWEEN 10 AND 16
	THEN 1
	ELSE 0
	END as midday,
	CASE WHEN EXTRACT(HOUR FROM r.refueling_time) BETWEEN 16 AND 22
		THEN 1
		ELSE 0
	END as afternoon,
	CASE WHEN EXTRACT(HOUR FROM r.refueling_time) BETWEEN 22 AND 24 OR  EXTRACT(HOUR FROM r.refueling_time) BETWEEN 0 AND 4
		THEN 1
		ELSE 0
	END as night,
	o.price as oilprice,
	r.rerun::int as app,
	EXTRACT(doy FROM r.refueling_time) - EXTRACT(doy FROM '2014-06-01 00:00:00'::timestamp) AS count,
	CASE WHEN r.fuel_type = 'e5' 
		THEN ROUND((r.price-0.6545-(r.price-(r.price/1.19)))::numeric, 4)
		ELSE ROUND((r.price-0.4704-(r.price-(r.price/1.19)))::numeric, 4)
	END AS net_price,
	CASE WHEN r.fuel_type = 'e5' 
		THEN 0.6545
		ELSE 0.4704
	END AS fuel_tax,
	CASE WHEN r.fuel_type = 'e5' 
		THEN ROUND((r.price-(r.price/1.19))::numeric, 4)
		ELSE ROUND((r.price-(r.price/1.19))::numeric, 4)
	END AS vat,
	r.price,
	CASE WHEN EXISTS(SELECT 1 FROM bab_stations WHERE id = r.station)
		THEN 1
		ELSE 0
	END as bab_station,
	CASE WHEN EXISTS(SELECT 1 FROM de_tt_stations_modified WHERE id = r.station AND brand IN (SELECT brand FROM brands))
		THEN 1
		ELSE 0
	END as brand,
	CASE WHEN r.fuel_type = 'e5' 
		THEN 1 
		ELSE 0 
	END AS fuel_type,
	SUBSTRING(s.rs FOR 5) AS rs_station,
	p.rs_start,
	p.rs_end
FROM de_sim_data_refill r
LEFT JOIN de_tt_stations_modified s ON (s.id = r.station)
LEFT JOIN LATERAL (
	SELECT price FROM de_sim_data_oilprice op
	WHERE op.day <= r.refueling_time::date 
	ORDER BY op.day DESC LIMIT 1
) o ON TRUE
LEFT JOIN LATERAL (
	SELECT rs_start, rs_end FROM de_sim_routes ro
	LEFT JOIN LATERAL (SELECT SUBSTRING(rs FOR 5) as rs_start FROM de_sim_points WHERE id = ro.start_point LIMIT 1) s ON TRUE
	LEFT JOIN LATERAL (SELECT SUBSTRING(rs FOR 5) as rs_end FROM de_sim_points WHERE id = ro.end_point LIMIT 1) e ON TRUE
	WHERE ro.id = r.c_id
LIMIT 1
) p ON TRUE