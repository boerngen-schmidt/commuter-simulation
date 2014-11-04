--- Add geometries to the gemeinden table
BEGIN;
UPDATE de_commuter_gemeinden AS cg
SET geom = keys.geom
FROM (
	SELECT rau_rs, geom
	FROM de_shp_gemeinden
) AS keys
WHERE cg.rs = keys.rau_rs;
COMMIT;

--- Add geometries to the kreise table

BEGIN;
UPDATE de_commuter_kreise AS ck
SET geom = keys.geom
FROM (
	SELECT rs, geom
	FROM de_shp_kreise
) AS keys
WHERE ck.rs = keys.rau_rs;
COMMIT;