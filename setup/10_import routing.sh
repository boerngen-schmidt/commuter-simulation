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

infoMsg "Preparing Database for routing"
psql -c "CREATE EXTENSION postgis" -d $DATABASE -U $USER
psql -c "CREATE EXTENSION pgrouting" -d $DATABASE -U $USER

function f_osm2pgrouting {
	warnMsg "Might FAIL!!!"
	
	read -p "Please enter password for Postgreql user  \"$USER\": " password
	osm2pgrouting -file $1 -conf /usr/share/osm2pgrouting/mapconfig_for_cars.xml -dbname $DATABASE -user $USER -host localhost -passwd $password
}

function f_osm2po {
	OSM2PO_HOME=$BASE/bin/osm2po
	while /bin/true
	do
		if [ ! -d $OSM2PO_HOME ]; then
			warnMsg "OSM2PO was not found!"
			read -e -p "Please input path to OSM2PO. [$OSM2PO_HOME]: " input
			OSM2PO_HOME=${input}
		else
			break
		fi
	done
	
	# Change to dir where config file is located
	cd $BASE/config/osm2po
	
	infoMsg "Creating road network"
	time java -Xmx12g -jar $OSM2PO_HOME/osm2po.jar prefix=de cmd=tjspg workDir=$TMPDIR/osm2po_import $1
	infoMsg "Importing OSM2PO network into database"
	time psql -U $USER -d $DATABASE -q -f "$TMPDIR/osm2po_import/de_2po_4pgr.sql"
	time psql -U $USER -d $DATABASE -q -f "$TMPDIR/osm2po_import/de_2po_vertex.sql"
	infoMsg "Running post import scripts ..."
	time psql -U $USER -d $DATABASE -q -f "$BASE/config/postgresql/post-import_osm2po.sql"
}

PS3="Choose OSM File for import: "
osmfile_choices=( $(find $BASE/data/osm -type f -iname "*.osm*") )
select choice in ${osmfile_choices[@]}
do
	if (( $REPLY > 0 && $REPLY <= ${#osmfile_choices[@]} )); then
		OSMFILE=$choice
		break
	else
		echo "Invailid choice, please select a OSM File"
	fi
	echo
	REPLY=
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
			echo
			REPLY=
			;;
	esac
done
	
cd $BASE

