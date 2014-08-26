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
osmfile_choices=($TMPDIR/*.osm*)
select choice in $osmfile_choices
do
	if (( $REPLY > 0 && $REPLY <= ${#osmfile_choices[@]} )); then
		if [[ ${choice: -4} == ".osm" ]]; then
			OSM_OPTS=""
		elif [[ ${choice: -4} == ".bz2" ]]; then
			OSM_OPTS=""
		elif [[ ${choice: -4} == ".pbf" ]]; then
			OSM_OPTS="-r pdf"
		fi
		OSMFILE=$choice
		break
	else
		echo "Invailid choice, please select a OSM File"
		REPLY=
	fi
done

if [ ! -f $OSMFILE ]; then
echo $OSMFILE
	echo "OSM File was not found!"
	exit 1
fi

OSM2PGSQL_OPTIONS="-c -d $DATABASE -U $USER -p de_osm -C 14336 -j $OSM_OPTS"

osm2pgsql $OSM2PGSQL_OPTIONS $OSMFILE