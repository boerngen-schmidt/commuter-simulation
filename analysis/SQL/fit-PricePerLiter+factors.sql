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
	to_char(refueling_time, 'Dy') as zeDay,
	to_char(refueling_time, 'HH24') as zeTime,
	CASE
		WHEN EXTRACT(HOUR FROM r.refueling_time) BETWEEN 5 AND 10 THEN 'morning'
		WHEN EXTRACT(HOUR FROM r.refueling_time) BETWEEN 11 AND 16 THEN 'midday'
		WHEN EXTRACT(HOUR FROM r.refueling_time) BETWEEN 17 AND 22 THEN 'afternoon'
		ELSE 'night'
	END as time_slotted,
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