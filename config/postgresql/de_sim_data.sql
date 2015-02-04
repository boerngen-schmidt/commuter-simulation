CREATE TABLE de_sim_data_commuter
(
    c_id INT NOT NULL,
    leaving_time TIME NOT NULL,
    route_home_distance DOUBLE PRECISION NOT NULL,
    route_work_distance DOUBLE PRECISION NOT NULL,
    error VARCHAR(32)
);
CREATE INDEX de_sim_data_commuter_c_id_idx ON de_sim_data_commuter (c_id);

CREATE TABLE de_sim_data_refill
(
    id SERIAL PRIMARY KEY NOT NULL,
    c_id INT,
    amount DOUBLE PRECISION,
    price DOUBLE PRECISION,
    time TIMESTAMP,
    station VARCHAR(255),
    type VARCHAR(10)
);
CREATE INDEX de_sim_data_refill_c_id_idx ON de_sim_data_refill (c_id);
