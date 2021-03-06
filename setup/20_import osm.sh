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
psql -q -c "CREATE EXTENSION btree_gist" -d $DATABASE -U $USER

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

OSM2PGSQL_OPTIONS="-c -s -d $DATABASE -U $USER -p de_osm -C 8192 --drop --unlogged --number-processes 8 -S $STYLEFILE -l -E 25832 $OSM_OPTS"

if [[ -e $BASE/bin/osm2pgsql && $(ynQuestion "Do you want to run local version of osm2pgsql?") ]]; then
	infoMsg "Runnung local version of osm2pgsql"
	time $BASE/bin/osm2pgsql $OSM2PGSQL_OPTIONS $OSMFILE
else
	infoMsg "Runnung system version of osm2pgsql"
	time osm2pgsql $OSM2PGSQL_OPTIONS $OSMFILE
fi

infoMsg "Running post-import SQL scripts"
time psql -q -f $BASE/config/postgresql/post-import_osm2pgsql.sql -d $DATABASE -U $USER
