#!/bin/bash

if [ ! $INSCRIPT ]; then
	exit 1
fi

if [ ! $(ynQuestion "Install system Packages?") ]; then
	infoMsg "Installing nessesary Packages"
	case $(currentDistribution) in
		$DIST_DEBIAN)
			sudo add-apt-repository -y ppa:georepublic/pgrouting >/dev/null 2>&1
			sudo apt-get -q update >/dev/null
		
			PACKAGES="postgresql postgresql-contrib postgis postgresql-9.3-pgrouting osm2pgrouting osm2pgsql pgadmin3 python-dev mysql-server mysql-client libmysqlclient-dev"
			sudo apt-get -q -y install $PACKAGES
			;;
		$DIST_GENTOO)
			PACKAGES="postgresql postgis pgrouting mysql virtualenv dev-python/pip net-libs/zeromq"
			doemerge $PACKAGES
			infoMsg "Set login path for mySQL"
			mysql_config_editor set --login-path=local --host=localhost --user=username --password
			;;
		*)
			warnMsg "Could not determine Linux distribution for installing needed packages"
			exit 1
			;;
	esac		
fi

infoMsg "Fetching OSM data"
if [ $(ynQuestion "Download latest OSM Germany Map? (PBF Format)") ]; then
	wget http://download.geofabrik.de/europe/germany-latest.osm.pbf -P $BASE/data/osm -N
else
	warnMsg "Skipped downloading OSM Data (PBF)"
fi

if [ $(ynQuestion "Download latest OSM Germany Map? (BZ2 Format)") ]; then
	wget http://download.geofabrik.de/europe/germany-latest.osm.bz2 -P $BASE/data/osm -N
else
	warnMsg "Skipped downloading OSM Data (BZ2)"
fi

infoMsg "Downloading OSM2PO"
if [ -d $BASE/bin/osm2po ]; then
	rm -rf $BASE/bin/osm2po
fi
wget -P $TMPDIR "http://osm2po.de/dld/osm2po-5.0.0.zip" --referer http://osm2po.de --content-disposition -N
unzip -q $TMPDIR/osm2po-5.0.0.zip -d $BASE/bin/osm2po
cd $BASE/bin/osm2po
ln -s osm2po-core-*-signed.jar osm2po.jar
