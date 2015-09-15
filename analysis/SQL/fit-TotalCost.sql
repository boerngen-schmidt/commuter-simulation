BEGIN;
CREATE TEMP TABLE bab_stations(id character varying PRIMARY KEY) ON COMMIT DROP;
INSERT INTO bab_stations
	SELECT id
	FROM de_tt_stations_modified
	WHERE LOWER(street) ~ '(a\\d+|a\\s+\\d+|bab|autohof|rasthof|autobahn|^a$)' OR LOWER(name) ~ 'bat';
CREATE TEMP TABLE brands (id character varying PRIMARY KEY) ON COMMIT DROP;
INSERT INTO brands
	SELECT id
	FROM de_tt_stations_modified
	WHERE lower(brand) IN (
		SELECT lower(brand)
		FROM de_tt_stations_modified
		WHERE LOWER(brand) NOT IN ('bft', 'freie tankstelle')
		GROUP BY brand
		HAVING COUNT(brand) > 200
	);
SELECT
	cost,
	app,
	fuel_type,
	refill_events,
	amount,
	bab_stations,
	brands,
	goodtime
FROM (
	SELECT
		c_id,
		rerun::int AS app,
		rerun,
		CASE WHEN fuel_type = 'e5'
			THEN 1
			ELSE 0
		END AS fuel_type
	FROM de_sim_data_commuter c1
) AS c
LEFT JOIN LATERAL (
	SELECT
		ROUND(SUM(amount)::numeric, 0) AS amount,
		SUM(goodtime) AS goodtime,
		ROUND(SUM(cost)::numeric, 0) AS cost,
		SUM(bab_station)::int AS bab_stations,
		SUM(brand)::int AS brands,
		COUNT(*)::int AS refill_events
	FROM (
		SELECT
			r.price * r.amount AS cost,
			r.amount,
			CASE WHEN EXTRACT(HOUR FROM r.refueling_time) BETWEEN 10 AND 18
				THEN 1
				ELSE 0
			END AS goodtime,
			CASE WHEN EXISTS(SELECT 1 FROM bab_stations WHERE id = r.station)
				THEN 1
				ELSE 0
			END AS bab_station,
			CASE WHEN EXISTS(SELECT 1 FROM brands WHERE id = r.station)
				THEN 1
				ELSE 0
			END AS brand
		FROM de_sim_data_refill r
		WHERE c.c_id = r.c_id AND c.rerun = r.rerun
	) r1
) r2 ON TRUE;
