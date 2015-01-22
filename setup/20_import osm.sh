#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi

DBEXISTS=`psql -At -c "SELECT count(*) FROM pg_database where datname='$DATABASE'" -d postgres -U $USER`
if [ ! $DBEXISTS ]; then
	echo
	echo -e "\e[31m##########################################"
	echo -e "\e[39mPlease run PostgreSQL configuration first!"
	echo -e "\e[31m##########################################\e[39m"
	echo
	exit
fi

echo "Preparing Database for OpenStreetMap Data ..."
psql -q -c "CREATE EXTENSION postgis" -d $DATABASE -U $USER
psql -q -c "CREATE EXTENSION hstore" -d $DATABASE -U $USER

PS3="Choose OSM File for import: "
osmfile_choices=( $(find $BASE/data/osm -type f -iname "*.osm*") )
select choice in ${osmfile_choices[@]}
do
	if (( $REPLY > 0 && $REPLY <= ${#osmfile_choices[@]} )); then
		if [[ ${choice: -4} == ".osm" ]]; then
			OSM_OPTS=""
		elif [[ ${choice: -4} == ".bz2" ]]; then
			OSM_OPTS=""
		elif [[ ${choice: -4} == ".pbf" ]]; then
			OSM_OPTS="-r pbf"
		fi
		OSMFILE=$choice
		break
	else
		warnMsg "Invailid choice, please select a OSM File"
		REPLY=
	fi
done

if [ ! -f $OSMFILE ]; then
	echo $OSMFILE
	warnMsg "OSM File was not found!"
	exit 1
fi

PS3="Choose style File for import: "
style_choices=( $(find $BASE/config/osm2pgsql -type f -iname "*.style") )
select choice in ${style_choices[@]}
do
	if (( $REPLY > 0 && $REPLY <= ${#osmfile_choices[@]} )); then
		STYLEFILE=$choice
		break
	else
		echo "Invailid choice, please select a style File"
	fi
	echo
	REPLY=
done

OSM2PGSQL_OPTIONS="--number-processes 8 -c -d $DATABASE -U $USER -p de_osm -C 12000 \
					-S $STYLEFILE -l \
					$OSM_OPTS"
if [ $(ynQuestion "Do you want to build osm2pgsql from sources?") ]; then
	# remove old stuff
	rm -rf $TMPDIR/osm2pgsql
	buildOSM2PGSQL

fi
if [ -e $BASE/bin/osm2pgsql ]; then
	infoMsg "Runnung local version of osm2pgsql"
	time $BASE/bin/osm2pgsql $OSM2PGSQL_OPTIONS $OSMFILE
else
	infoMsg "Runnung system version of osm2pgsql"
	time osm2pgsql $OSM2PGSQL_OPTIONS $OSMFILE
fi

infoMsg "Running post-import SQL scripts"
psql -q -f $BASE/config/postgresql/post-import_de_osm_polygon.sql -d $DATABASE -U $USER
psql -q -f $BASE/config/postgresql/post-import_de_osm_roads.sql -d $DATABASE -U $USER
