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
	refill_events,
	bab_stations::NUMERIC / refill_events as bab_stations,
	brands::NUMERIC / refill_events as brands,
  	morning::NUMERIC / refill_events as mornings,
  	midday::NUMERIC / refill_events as middays,
  	afternoon::NUMERIC / refill_events as afternoons,
  	night::NUMERIC / refill_events as nights,
  	mon::NUMERIC / refill_events as mon,
	tue::NUMERIC / refill_events as tue,
  	wed::NUMERIC / refill_events as wed,
  	thu::NUMERIC / refill_events as thu,
  	fri::NUMERIC / refill_events as fri,
  	sat::NUMERIC / refill_events as sat
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
	WHERE c_id IN (SELECT c_id FROM de_sim_data_commuter_sampled)
) AS c
LEFT JOIN LATERAL (
	SELECT
		SUM(morning) AS morning,
		SUM(midday) AS midday,
		SUM(afternoon) AS afternoon,
		SUM(night) AS night,
		SUM(mon) AS mon,
		SUM(tue) AS tue,
		SUM(wed) AS wed,
		SUM(thu) AS thu,
		SUM(fri) AS fri,
		SUM(sat) AS sat,
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
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 1
				THEN 1
				ELSE 0
			END AS mon,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 2
				THEN 1
				ELSE 0
			END AS tue,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 3
				THEN 1
				ELSE 0
			END AS wed,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 4
				THEN 1
				ELSE 0
			END AS thu,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 5
				THEN 1
				ELSE 0
			END AS fri,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 6
				THEN 1
				ELSE 0
			END AS sat,
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
