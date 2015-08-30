-- Totale Ausgaben für Kraftstoff
SELECT * FROM (SELECT SUM(amount*price) as app FROM de_sim_data_refill WHERE rerun) a
 LEFT JOIN LATERAL (SELECT SUM(amount*price) as noapp FROM de_sim_data_refill WHERE NOT rerun) b ON TRUE 
 
-- Gesamt gefahrene Strecke in der Simulation
SELECT * FROM (SELECT SUM(driven_distance) as app FROM de_sim_data_commuter WHERE rerun) a
 LEFT JOIN LATERAL (SELECT SUM(driven_distance) as noapp FROM de_sim_data_commuter WHERE NOT rerun) b ON TRUE 

-- Ausgaben für Kraftstoff aufgeschlüsselt nach Distanzen
SELECT * FROM (
 SELECT min::float, max::float FROM (VALUES (0,5), (5,10), (10,25), (25,50), (50,999)) as d("min", "max")
) as p1
LEFT JOIN LATERAL (
 SELECT SUM (price*amount) FROM de_sim_data_refill WHERE c_id IN (
  SELECT c_id FROM de_sim_data_commuter c WHERE (route_work_distance > p1.min AND route_work_distance <= p1.max AND c.rerun)
  )
  AND rerun
) as p2 ON TRUE
LEFT JOIN LATERAL (
 SELECT SUM (price*amount) FROM de_sim_data_refill WHERE c_id IN (
  SELECT c_id FROM de_sim_data_commuter c WHERE (route_work_distance > p1.min AND route_work_distance <= p1.max AND NOT c.rerun)
  )
  AND NOT rerun
) as p3 ON TRUE