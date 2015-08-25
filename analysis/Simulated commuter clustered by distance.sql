SELECT min, max, noapp, app FROM (
	SELECT column1 as min, column2 as max FROM (VALUES (0, 5), (5, 10), (10, 25), (25, 50), (50, 200)) as a
) a
LEFT JOIN LATERAL (
	SELECT COUNT(*) as noapp FROM de_sim_data_commuter WHERE NOT rerun AND route_work_distance >= min and route_work_distance < max
) b ON TRUE 
LEFT JOIN LATERAL (
	SELECT COUNT(*) as app FROM de_sim_data_commuter WHERE rerun AND route_work_distance >= min and route_work_distance < max
) c ON TRUE 