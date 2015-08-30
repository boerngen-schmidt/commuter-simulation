-- SELECT * FROM de_tt_stations_modified WHERE brand IN (SELECT brand FROM (SELECT brand, COUNT(brand) FROM de_tt_stations_modified GROUP BY brand ORDER BY count DESC LIMIT 17) as limiting)

SELECT id, brand FROM de_tt_stations_modified WHERE LOWER(street) ~ '(a\d+|a \d+|bab|autohof|rasthof)';
