-- Zwei Stichproben T-Test
SELECT * FROM (
  SELECT c_id FROM de_sim_data_commuter WHERE NOT rerun
) c
LEFT JOIN LATERAL (
SELECT SUM(amount*price) as noapp FROM de_sim_data_refill WHERE c_id = c.c_id AND NOT rerun
) p1 ON TRUE
LEFT JOIN LATERAL (
SELECT SUM(amount*price) as app FROM de_sim_data_refill WHERE c_id = c.c_id AND rerun
) p2 ON TRUE

-- Zwei Stichproben T-Test (Preis pro Kilometer)
SELECT c_id, noapp::float/k.driven_distance AS ppkm_noapp, app::float/n.driven_distance AS ppkm_app FROM (
	(
	  SELECT c_id, driven_distance FROM de_sim_data_commuter WHERE NOT rerun ORDER BY c_id
	) c1
	LEFT JOIN LATERAL (
	  SELECT SUM(amount*price) as noapp FROM de_sim_data_refill WHERE c_id = c1.c_id AND NOT rerun
	) p1 ON TRUE
) k
LEFT JOIN (
	(
	  SELECT c_id, driven_distance FROM de_sim_data_commuter WHERE rerun ORDER BY c_id
	) c2
	LEFT JOIN LATERAL (
	  SELECT SUM(amount*price) as app FROM de_sim_data_refill WHERE c_id = c2.c_id AND rerun
	) p2 ON TRUE
) n USING (c_id)
WHERE app IS NOT NULL AND noapp IS NOT NULL