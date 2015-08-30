SELECT c_id, COUNT(c_id), d.route_work_distance
FROM de_sim_data_refill 
LEFT JOIN (SELECT c_id, route_work_distance FROM de_sim_data_commuter) d USING(c_id)
WHERE amount >= 50.0 AND rerun
GROUP BY c_id, d.route_work_distance
HAVING  d.route_work_distance <= 50.0
ORDER BY  d.route_work_distance
