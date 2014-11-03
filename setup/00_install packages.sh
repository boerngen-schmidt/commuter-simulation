#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi

infoMsg "Installing nessesary Packages"
case currentDistribution in
	$DIST_DEBIAN)
		sudo add-apt-repository -y ppa:georepublic/pgrouting >/dev/null 2>&1
		sudo apt-get -q update >/dev/null
		
		PACKAGES="postgresql postgresql-contrib postgis postgresql-9.3-pgrouting osm2pgrouting osm2pgsql pgadmin3 python-dev mysql-server mysql-client libmysqlclient-dev"
		sudo apt-get -q -y install $PACKAGES
		;;
	$DIST_GENTOO)
		PACKAGES="postgres-server postgis pgrouting	mysql"
		emerge $PACKAGES
		if [ $? -ne 0 ]; then
			errorMsg "Please fix emerge errors"
			exit 1
		;;
	*)
		errorMsg "Could not determine Linux distribution for installing needed packages"
		exit 1
		;;
esac		

infoMsg "Fetching OSM data"
read -p "Download latest OSM Germany Map? [y/N]: " yn
case $yn in
	[Yy]* ) 
		wget http://download.geofabrik.de/europe/germany-latest.osm.pbf -P $BASE/data/osm -N
		wget http://download.geofabrik.de/europe/germany-latest.osm.bz2 -P $BASE/data/osm -N
		;;
	* ) warnMsg "Skipped downloading OSM Data";;
esac

infoMsg "Downloading OSM2PO"
wget -P $TMPDIR "http://osm2po.de/download.php?lnk=osm2po-4.8.8.zip" --referer http://osm2po.de --content-disposition -N
unzip $TMPDIR/osm2po-4.8.8.zip -d $BASE/bin/osm2po
