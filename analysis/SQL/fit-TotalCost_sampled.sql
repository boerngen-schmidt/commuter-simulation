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
	bab_stations::NUMERIC / refilling_events as bab_stations,
	brands::NUMERIC / refilling_events as brands,
  morning::NUMERIC / refilling_events as mornings,
  midday::NUMERIC / refilling_events as middays,
  afternoon::NUMERIC / refilling_events as afternoos,
  night::NUMERIC / refilling_events as nigths
FROM (
	SELECT
		c_id,
		rerun::int AS app,
		rerun,
		ROUND(route_work_distance::numeric, 2) AS route_length,
		ROUND(driven_distance::numeric, 2) AS driven_distance,
		array_length(filling_stations, 1) AS filling_stations,
		p.rs_start,
		p.rs_end,
		CASE WHEN fuel_type = 'e5'
			THEN 1
			ELSE 0
		END AS fuel_type
	FROM de_sim_data_commuter c1
	LEFT JOIN LATERAL (
		SELECT
			rs_start,
			rs_end
		FROM de_sim_routes ro
		LEFT JOIN LATERAL (SELECT SUBSTRING(rs FOR 5) AS rs_start FROM de_sim_points WHERE id = ro.start_point LIMIT 1) s ON TRUE
		LEFT JOIN LATERAL (SELECT SUBSTRING(rs FOR 5) AS rs_end FROM de_sim_points WHERE id = ro.end_point LIMIT 1) e ON TRUE
		WHERE ro.id = c1.c_id
		LIMIT 1
	) p ON TRUE
	WHERE c_id IN (SELECT c_id FROM de_sim_data_commuter_sampled)
) AS c
LEFT JOIN LATERAL (
	SELECT
		SUM(morning) AS morning,
		SUM(midday) AS midday,
		SUM(afternoon) AS afternoon,
		SUM(night) AS night,
		ROUND(SUM(cost)::numeric, 2) AS cost,
		SUM(bab_station)::int AS bab_stations,
		SUM(brand)::int AS brands,
		COUNT(*)::int AS refill_events
	FROM (
		SELECT
			CASE WHEN EXTRACT(HOUR FROM r.refueling_time) BETWEEN 5 AND 10
				THEN 1
				ELSE 0
			END AS morning,
			CASE WHEN EXTRACT(HOUR FROM r.refueling_time) BETWEEN 11 AND 16
				THEN 1
				ELSE 0
			END AS midday,
			CASE WHEN EXTRACT(HOUR FROM r.refueling_time) BETWEEN 17 AND 22
				THEN 1
				ELSE 0
			END AS afternoon,
			CASE WHEN EXTRACT(HOUR FROM r.refueling_time) BETWEEN 23 AND 24 OR  EXTRACT(HOUR FROM r.refueling_time) BETWEEN 0 AND 4
				THEN 1
				ELSE 0
			END AS night,
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
