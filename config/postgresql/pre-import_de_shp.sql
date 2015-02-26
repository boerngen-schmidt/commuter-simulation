BEGIN;
    DROP TABLE IF EXISTS de_shp CASCADE;
    CREATE TABLE de_shp
    (
      gid serial NOT NULL,
      objectid integer,
      use numeric,
      rs character varying(12) UNIQUE,
      gf numeric,
      rau_rs character varying(12),
      gen character varying(50),
      des character varying(75),
      ags character varying(12),
      rs_alt character varying(20),
      wirksamkei timestamp with time zone,
      debkg_id character varying(16),
      length numeric,
      shape_leng numeric,
      shape_area numeric,
      geom geometry(MultiPolygon,25832),
      CONSTRAINT de_shp_pkey PRIMARY KEY (gid)
    );

    DROP TABLE IF EXISTS de_shp_bundeslaender;
    CREATE TABLE de_shp_bundeslaender (
        CONSTRAINT de_shp_bundeslaender_pkey PRIMARY KEY (gid)
    ) INHERITS (de_shp);

    DROP TABLE IF EXISTS de_shp_kreise;
    CREATE TABLE de_shp_kreise (
        CONSTRAINT de_shp_kreise_pkey PRIMARY KEY (gid)
    ) INHERITS (de_shp);

    DROP TABLE IF EXISTS de_shp_gemeinden;
    CREATE TABLE de_shp_gemeinden (
        CONSTRAINT de_shp_gemeinden_pkey PRIMARY KEY (gid)
    ) INHERITS (de_shp);

    DROP TABLE IF EXISTS de_shp_verwaltungsgemeinschaften;
    CREATE TABLE de_shp_verwaltungsgemeinschaften (
        CONSTRAINT de_shp_verwaltungsgemeinschaften_pkey PRIMARY KEY (gid)
    ) INHERITS (de_shp);
COMMIT;