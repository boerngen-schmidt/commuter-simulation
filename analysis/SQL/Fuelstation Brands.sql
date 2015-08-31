SELECT brand, count(brand)
FROM de_tt_stations_modified
WHERE LOWER(brand) NOT IN ('bft', 'freie tankstelle')
GROUP BY brand 
--HAVING COUNT(brand) > 200;
ORDER BY COUNT(brand) desc;
