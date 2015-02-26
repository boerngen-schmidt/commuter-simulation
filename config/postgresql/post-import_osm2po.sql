BEGIN;
    ALTER TABLE de_2po_4pgr ALTER geom_way TYPE geometry(LineString,25832) USING st_transform(geom_way, 25832);
    ALTER TABLE de_2po_vertex ALTER geom_vertex TYPE geometry(Point,25832) USING st_transform(geom_vertex, 25832);

    CREATE INDEX ON public.de_2po_4pgr USING gist (geom_way);
    CREATE INDEX ON public.de_2po_vertex USING gist (geom_vertex);
COMMIT;