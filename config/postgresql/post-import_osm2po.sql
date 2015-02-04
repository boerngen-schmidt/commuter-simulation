CREATE INDEX ON public.de_2po_4pgr USING gist (geom_way);
CREATE INDEX ON public.de_2po_vertex USING gist (geom_vertex);