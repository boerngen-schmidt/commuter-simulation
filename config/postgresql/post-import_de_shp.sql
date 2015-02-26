BEGIN;
    DROP INDEX IF EXISTS de_shp_bundeslaender_rs_index;
    CREATE INDEX de_shp_bundeslaender_rs_index ON de_shp_bundeslaender USING btree (rs COLLATE pg_catalog."default");

    DROP INDEX IF EXISTS de_shp_kreise_rs_index;
    CREATE INDEX de_shp_kreise_rs_index ON de_shp_kreise USING btree (rs COLLATE pg_catalog."default");

    DROP INDEX IF EXISTS de_shp_gemeinden_rs_index;
    CREATE INDEX de_shp_gemeinden_rs_index ON de_shp_gemeinden USING btree (rs COLLATE pg_catalog."default");
COMMIT;