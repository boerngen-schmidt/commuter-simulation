-- Sample for 20000 Commuter

INSERT INTO de_sim_data_commuter_sampled 
SELECT c_id 
FROM de_sim_data_commuter 
WHERE route_work_distance > 0 AND route_work_distance < 5
ORDER BY RANDOM()
LIMIT (0.29*20000)::int;

INSERT INTO de_sim_data_commuter_sampled 
SELECT c_id 
FROM de_sim_data_commuter 
WHERE route_work_distance >= 5 AND route_work_distance < 10
ORDER BY RANDOM()
LIMIT (0.197*20000)::int;

INSERT INTO de_sim_data_commuter_sampled 
SELECT c_id 
FROM de_sim_data_commuter 
WHERE route_work_distance >= 10 AND route_work_distance < 25
ORDER BY RANDOM()
LIMIT (0.266*20000)::int;

INSERT INTO de_sim_data_commuter_sampled 
SELECT c_id 
FROM de_sim_data_commuter 
WHERE route_work_distance >= 25 AND route_work_distance < 50
ORDER BY RANDOM()
LIMIT (0.125*20000)::int;

INSERT INTO de_sim_data_commuter_sampled 
SELECT c_id 
FROM de_sim_data_commuter 
WHERE route_work_distance >= 50
ORDER BY RANDOM()
LIMIT (0.044*20000)::int;
