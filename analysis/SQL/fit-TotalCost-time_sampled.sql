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
SELECT * FROM (
	SELECT
		c_id,
		rerun::int AS app,
		rerun,
		ROUND(route_work_distance::numeric, 2) AS route,
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
		SUM(mon_morning)::int 	AS mon_morning,
		SUM(mon_midday)::int 	AS mon_midday,
		SUM(mon_afternoon)::int AS mon_afternoon,
		SUM(mon_night)::int 	AS mon_night,
		SUM(tue_morning)::int 	AS tue_morning,
		SUM(tue_midday)::int 	AS tue_midday,
		SUM(tue_afternoon)::int AS tue_afternoon,
		SUM(tue_night)::int 	AS tue_night,
		SUM(wed_morning)::int 	AS wed_morning,
		SUM(wed_midday)::int 	AS wed_midday,
		SUM(wed_afternoon)::int AS wed_afternoon,
		SUM(wed_night)::int 	AS wed_night,
		SUM(thu_morning)::int 	AS thu_morning,
		SUM(thu_midday)::int 	AS thu_midday,
		SUM(thu_afternoon)::int AS thu_afternoon,
		SUM(thu_night)::int 	AS thu_night,
		SUM(fri_morning)::int 	AS fri_morning,
		SUM(fri_midday)::int 	AS fri_midday,
		SUM(fri_afternoon)::int AS fri_afternoon,
		SUM(fri_night)::int 	AS fri_night,
		SUM(sat_morning)::int 	AS sat_morning,
		SUM(sat_midday)::int 	AS sat_midday,
		SUM(sat_afternoon)::int AS sat_afternoon,
		SUM(sat_night)::int 	AS sat_night,
		ROUND(SUM(cost)::numeric, 2) AS cost,
		SUM(bab_station)::int AS bab_station,
		SUM(brand)::int AS brand,
		COUNT(*)::int AS refill_events
	FROM (
		SELECT
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 1 AND EXTRACT(HOUR FROM r.refueling_time) BETWEEN 5 AND 10
				THEN 1
				ELSE 0
			END AS mon_morning,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 1 AND EXTRACT(HOUR FROM r.refueling_time) BETWEEN 11 AND 16
				THEN 1
				ELSE 0
			END AS mon_midday,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 1 AND EXTRACT(HOUR FROM r.refueling_time) BETWEEN 17 AND 22
				THEN 1
				ELSE 0
			END AS mon_afternoon,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 1 AND (EXTRACT(HOUR FROM r.refueling_time) BETWEEN 23 AND 24 OR  EXTRACT(HOUR FROM r.refueling_time) BETWEEN 0 AND 4)
				THEN 1
				ELSE 0
			END AS mon_night,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 2 AND EXTRACT(HOUR FROM r.refueling_time) BETWEEN 5 AND 10
				THEN 1
				ELSE 0
			END AS tue_morning,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 2 AND EXTRACT(HOUR FROM r.refueling_time) BETWEEN 11 AND 16
				THEN 1
				ELSE 0
			END AS tue_midday,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 2 AND EXTRACT(HOUR FROM r.refueling_time) BETWEEN 17 AND 22
				THEN 1
				ELSE 0
			END AS tue_afternoon,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 2 AND (EXTRACT(HOUR FROM r.refueling_time) BETWEEN 23 AND 24 OR  EXTRACT(HOUR FROM r.refueling_time) BETWEEN 0 AND 4)
				THEN 1
				ELSE 0
			END AS tue_night,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 3 AND EXTRACT(HOUR FROM r.refueling_time) BETWEEN 5 AND 10
				THEN 1
				ELSE 0
			END AS wed_morning,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 3 AND EXTRACT(HOUR FROM r.refueling_time) BETWEEN 11 AND 16
				THEN 1
				ELSE 0
			END AS wed_midday,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 3 AND EXTRACT(HOUR FROM r.refueling_time) BETWEEN 17 AND 22
				THEN 1
				ELSE 0
			END AS wed_afternoon,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 3 AND (EXTRACT(HOUR FROM r.refueling_time) BETWEEN 23 AND 24 OR  EXTRACT(HOUR FROM r.refueling_time) BETWEEN 0 AND 4)
				THEN 1
				ELSE 0
			END AS wed_night,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 4 AND EXTRACT(HOUR FROM r.refueling_time) BETWEEN 5 AND 10
				THEN 1
				ELSE 0
			END AS thu_morning,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 4 AND EXTRACT(HOUR FROM r.refueling_time) BETWEEN 11 AND 16
				THEN 1
				ELSE 0
			END AS thu_midday,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 4 AND EXTRACT(HOUR FROM r.refueling_time) BETWEEN 17 AND 22
				THEN 1
				ELSE 0
			END AS thu_afternoon,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 4 AND (EXTRACT(HOUR FROM r.refueling_time) BETWEEN 23 AND 24 OR  EXTRACT(HOUR FROM r.refueling_time) BETWEEN 0 AND 4)
				THEN 1
				ELSE 0
			END AS thu_night,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 5 AND EXTRACT(HOUR FROM r.refueling_time) BETWEEN 5 AND 10
				THEN 1
				ELSE 0
			END AS fri_morning,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 5 AND EXTRACT(HOUR FROM r.refueling_time) BETWEEN 11 AND 16
				THEN 1
				ELSE 0
			END AS fri_midday,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 5 AND EXTRACT(HOUR FROM r.refueling_time) BETWEEN 17 AND 22
				THEN 1
				ELSE 0
			END AS fri_afternoon,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 5 AND (EXTRACT(HOUR FROM r.refueling_time) BETWEEN 23 AND 24 OR  EXTRACT(HOUR FROM r.refueling_time) BETWEEN 0 AND 4)
				THEN 1
				ELSE 0
			END AS fri_night,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 6 AND EXTRACT(HOUR FROM r.refueling_time) BETWEEN 5 AND 10
				THEN 1
				ELSE 0
			END AS sat_morning,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 6 AND EXTRACT(HOUR FROM r.refueling_time) BETWEEN 11 AND 16
				THEN 1
				ELSE 0
			END AS sat_midday,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 6 AND EXTRACT(HOUR FROM r.refueling_time) BETWEEN 17 AND 22
				THEN 1
				ELSE 0
			END AS sat_afternoon,
			CASE WHEN EXTRACT(isodow FROM r.refueling_time) = 6 AND (EXTRACT(HOUR FROM r.refueling_time) BETWEEN 23 AND 24 OR  EXTRACT(HOUR FROM r.refueling_time) BETWEEN 0 AND 4)
				THEN 1
				ELSE 0
			END AS sat_night,
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
