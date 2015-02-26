#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi

cd $BASE/data/shape/vg250_zensus2011.utm32

infoMsg "Running pre-import script"
psql -U $USER -d $DATABASE -q -f $BASE/config/postgresql/pre-import_de_shp.sql

infoMsg "Import Bundesländer"
shp2pgsql -I -W 'LATIN1' -s 25832 -a VG250_Bundeslaender.shp de_shp_bundeslaender | psql -U $USER -d $DATABASE -q

infoMsg "Import Kreise"
shp2pgsql -I -W 'LATIN1' -s 25832 -a VG250_Kreise.shp de_shp_kreise | psql -U $USER -d $DATABASE -q

infoMsg "Import Gemeinden"
shp2pgsql -I -W 'LATIN1' -s 25832 -a VG250_Gemeinden.shp de_shp_gemeinden | psql -U $USER -d $DATABASE -q

infoMsg "Import Verwaltungsgemeinschaften"
shp2pgsql -I -W 'LATIN1' -s 25832 -a VG250_Verwaltungsgemeinschaften.shp de_shp_verwaltungsgemeinschaften | psql -U $USER -d $DATABASE -q

infoMsg "Running post-import script"
psql -U $USER -d $DATABASE -q -f $BASE/config/postgresql/post-import_de_shp.sql
cd $BASE