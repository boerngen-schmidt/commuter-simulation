WITH
	bab_stations AS(
		SELECT id
		FROM de_tt_stations_modified
		WHERE LOWER(street) ~ '(a\\d+|a\\s+\\d+|bab|autohof|rasthof|autobahn|^a$)' OR LOWER(name) ~ 'bat'
	),
	brands AS(
		SELECT brand, count(brand)
		FROM de_tt_stations_modified
		WHERE LOWER(brand) NOT IN ('bft', 'freie tankstelle')
		GROUP BY brand
		HAVING COUNT(brand) > 200
	)
SELECT
	cost,
	app,
	driven_distance,
	fuel_type,
	filling_stations,
	route_length,
	refill_events,
	bab_stations::NUMERIC / refill_events as bab_stations,
	brands::NUMERIC / refill_events as brands,
  	goodtime::NUMERIC / refill_events as goodtime
FROM (
	SELECT
		c_id,
		rerun::int AS app,
		rerun,
		ROUND(route_work_distance::numeric, 2) AS route_length,
		ROUND(driven_distance::numeric, 2) AS driven_distance,
		array_length(filling_stations, 1) AS filling_stations,
		CASE WHEN fuel_type = 'e5'
			THEN 1
			ELSE 0
		END AS fuel_type
	FROM de_sim_data_commuter c1
) AS c
LEFT JOIN LATERAL (
	SELECT
		SUM(goodtime) AS goodtime,
		ROUND(SUM(cost)::numeric, 2) AS cost,
		SUM(bab_station)::int AS bab_stations,
		SUM(brand)::int AS brands,
		COUNT(*)::int AS refill_events
	FROM (
		SELECT
			CASE WHEN EXTRACT(HOUR FROM r.refueling_time) BETWEEN 10 AND 21
				THEN 1
				ELSE 0
			END AS goodtime,
			r.price * r.amount AS cost,
			CASE WHEN EXISTS(SELECT 1 FROM bab_stations WHERE id = r.station)
				THEN 1
				ELSE 0
			END AS bab_station,
			CASE WHEN EXISTS(SELECT 1 FROM de_tt_stations_modified WHERE id = r.station AND brand IN (SELECT brand FROM brands))
				THEN 1
				ELSE 0
			END AS brand
		FROM de_sim_data_refill r
		WHERE c.c_id = r.c_id AND c.rerun = r.rerun
	) r1
) r2 ON TRUE
