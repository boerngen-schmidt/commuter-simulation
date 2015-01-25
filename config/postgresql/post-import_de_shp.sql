SELECT AddGeometryColumn('de_shp', 'geom_meter', 900913, 'MultiPolygon', 2);
UPDATE de_shp SET geom_meter = ST_Transform(geom, 900913);
CREATE INDEX de_shp_bundeslaender_geom_meter_idx ON public.de_shp_bundeslaender USING gist(geom_meter);
CREATE INDEX de_shp_gemeinden_geom_meter_idx ON public.de_shp_gemeinden USING gist(geom_meter);
CREATE INDEX de_shp_kreise_geom_meter_idx ON public.de_shp_kreise USING gist(geom_meter);
CREATE INDEX de_shp_verwaltungsgemeinschaften_geom_meter_idx ON public.de_shp_verwaltungsgemeinschaften USING gist(geom_meter);