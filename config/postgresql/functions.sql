CREATE OR REPLACE FUNCTION RandomPointsInPolygon(geom geometry, num_points integer)
	RETURNS SETOF geometry AS
$BODY$DECLARE
	target_proportion numeric;
	n_ret integer := 0;
	loops integer := 0;
	x_min float8;
	y_min float8;
	x_max float8;
	y_max float8;
	srid integer;
	rpoint geometry;
BEGIN
  -- Get envelope and SRID of source polygon
  SELECT ST_XMin(geom), ST_YMin(geom), ST_XMax(geom), ST_YMax(geom), ST_SRID(geom)
	INTO x_min, y_min, x_max, y_max, srid;
  -- Get the area proportion of envelope size to determine if a
  -- result can be returned in a reasonable amount of time
  SELECT ST_Area(geom)/ST_Area(ST_Envelope(geom)) INTO target_proportion;
  RAISE DEBUG 'geom: SRID %, NumGeometries %, NPoints %, area proportion within envelope %',
				srid, ST_NumGeometries(geom), ST_NPoints(geom),
				round(100.0*target_proportion, 2) || '%';
  IF target_proportion < 0.0001 THEN
	RAISE EXCEPTION 'Target area proportion of geometry is too low (%)', 
					100.0*target_proportion || '%';
  END IF;
  RAISE DEBUG 'bounds: % % % %', x_min, y_min, x_max, y_max;
  
  WHILE n_ret < num_points LOOP
	loops := loops + 1;
	SELECT ST_SetSRID(ST_MakePoint(random()*(x_max - x_min) + x_min,
								   random()*(y_max - y_min) + y_min),
					  srid) INTO rpoint;
	IF ST_Contains(geom, rpoint) THEN
	  n_ret := n_ret + 1;
	  RETURN NEXT rpoint;
	END IF;
  END LOOP;
  RAISE DEBUG 'determined in % loops (% efficiency)', loops, round(100.0*num_points/loops, 2) || '%';
END$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;
ALTER FUNCTION RandomPointsInPolygon(geometry, integer) OWNER TO benjamin;

--
--DROP FUNCTION pgr_fromAtoB(varchar, double precision, double precision, 
--							 double precision, double precision);

CREATE OR REPLACE FUNCTION pgr_fromAtoB(
				IN tbl varchar,
				IN x1 double precision,
				IN y1 double precision,
				IN x2 double precision,
				IN y2 double precision,
				OUT seq integer,
				OUT gid integer,
				OUT name text,
				OUT heading double precision,
				OUT cost double precision,
				OUT geom geometry
		)
		RETURNS SETOF record AS
$BODY$
DECLARE
		sql		text;
		rec		record;
		source	integer;
		target	integer;
		point	integer;
		
BEGIN
	-- Find nearest node
	EXECUTE 'SELECT id::integer FROM ways_vertices_pgr 
			ORDER BY the_geom <-> ST_GeometryFromText(''POINT(' 
			|| x1 || ' ' || y1 || ')'',4326) LIMIT 1' INTO rec;
	source := rec.id;
	
	EXECUTE 'SELECT id::integer FROM ways_vertices_pgr 
			ORDER BY the_geom <-> ST_GeometryFromText(''POINT(' 
			|| x2 || ' ' || y2 || ')'',4326) LIMIT 1' INTO rec;
	target := rec.id;

	-- Shortest path query (TODO: limit extent by BBOX) 
		seq := 0;
		sql := 'SELECT gid, the_geom, name, cost, source, target, 
				ST_Reverse(the_geom) AS flip_geom FROM ' ||
						'pgr_dijkstra(''SELECT gid as id, source::int, target::int, '
										|| 'length::float AS cost FROM '
										|| quote_ident(tbl) || ''', '
										|| source || ', ' || target 
										|| ' , false, false), '
								|| quote_ident(tbl) || ' WHERE id2 = gid ORDER BY seq';

	-- Remember start point
		point := source;

		FOR rec IN EXECUTE sql
		LOOP
		-- Flip geometry (if required)
		IF ( point != rec.source ) THEN
			rec.the_geom := rec.flip_geom;
			point := rec.source;
		ELSE
			point := rec.target;
		END IF;

		-- Calculate heading (simplified)
		EXECUTE 'SELECT degrees( ST_Azimuth( 
				ST_StartPoint(''' || rec.the_geom::text || '''),
				ST_EndPoint(''' || rec.the_geom::text || ''') ) )' 
			INTO heading;

		-- Return record
				seq		:= seq + 1;
				gid		:= rec.gid;
				name	:= rec.name;
				cost	:= rec.cost;
				geom	:= rec.the_geom;
				RETURN NEXT;
		END LOOP;
		RETURN;
END;
$BODY$
LANGUAGE 'plpgsql' VOLATILE STRICT;