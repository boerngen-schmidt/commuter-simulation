#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi

DATABASE="spritsim"

# Check if database exists. if so drop it and create it again
DBEXISTS=`psql -At -c "SELECT count(*) FROM pg_database where datname='$DATABASE'" -d postgres -U $USER`
if [ $DBEXISTS == 1 ]; then
	echo "Dropping database \"$DATABASE\" ..."
	dropdb -U $USER --if-exists $DATABASE
fi

echo "Creating Database for routing ..."
createdb -U $USER -E UTF8 -O $USER $DATABASE
psql -c "CREATE EXTENSION postgis" -d $DATABASE -U $USER
psql -c "CREATE EXTENSION pgrouting" -d $DATABASE -U $USER

function f_osm2pgrouting {
	echo "Might FAIL!!!"
	osm2pgrouting -file $1 -conf /usr/share/osm2pgrouting/mapconfig_for_cars.xml -dbname $DATABASE -user $USER -host localhost
}

function f_osm2po {
	OSM2PO_HOME=$BASE/osm2po
	read -e -p "Please input path to OSM2PO. [$OSM2PO_HOME]: " input
	OSM2PO_HOME=${input:-$OSM2PO_HOME}

	if [ ! -d $OSM2PO_HOME ]; then
		echo "OSM2PO was not found!"
		exit 1
	fi

	java -Xmx12g -jar $OSM2PO_HOME/osm2po-core-4.8.8-signed.jar prefix=de cmd=tjspg tileSize=x workDir=$BASE/src/osm2po_import $1
	echo; echo;
	echo "Importing OSM2PO network into database ..."
	time psql -U $USER -d $DATABASE -q -f "/home/benjamin/Dokumente/Masterthesis/src/osm2po_import/de_2po_4pgr.sql"
}

PS3="Choose OSM File for import: "
osmfile_choices=($BASE/src/*.osm*)
select choice in $osmfile_choices
do
	if (( $REPLY > 0 && $REPLY <= ${#osmfile_choices[@]} )); then
		OSMFILE=$choice
		break
		;;
	else
		echo "Invailid choice, please select a OSM File"
	fi
done

PS3="Choose method to import OSM data for routing: "
select choice in "OSM2PO" "osm2pgrouting" "Skip"
do
	case $REPLY in
		1)
			f_osm2po $OSMFILE
			break
			;;
		2)
			f_osm2pgrouting $OSMFILE
			break
			;;
		3)
			echo "Skipping Routing Import."
			break
			;;
		*)
			echo "WAZZZUP with you?! No Choice? Try again!"
			;;
	esac
done
	
	

